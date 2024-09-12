#!/usr/bin/python3

import re
import json
from copy import deepcopy
from openai import OpenAI
from infra_ai_service.config.config import settings
from infra_ai_service.service.spec_repair.utils import (
    gen_func_description,
    repair_spec,
    repair_spec_pro,
    repair_spec_impl,
    get_patch,
    save_log,
)

SYSTEM_PROMPT = ("你是一位经验丰富RPM软件包构建人员，"
                 "你的任务是根据提供的spec脚本和报错日志修复spec脚本，"
                 "以解决构建过程中出现的问题。")

PROMPT_TEMPLATE = """
spec脚本：
{spec}

报错日志：
{log}
"""

SYSTEM_PROMPT_PRO = """
## 任务：根据提供的spec脚本、报错日志定位问题，并通过项目文档给出修改建议，给出的代码中附带行号

## 输入格式：

spec脚本：
<spec脚本>

报错日志：
<报错日志>

项目文档：
<项目文档>

## 输出格式：

问题定位：
<问题定位>

修改建议：
<修改建议>

"""

PROMPT_TEMPLATE_PRO_1 = """
spec脚本：
{spec}

报错日志：
{log}

项目文档：
{doc}
"""

PROMPT_TEMPLATE_PRO_2 = """
## 任务：请根据提供的spec脚本、问题定位和修改建议修复spec脚本，以解决构建过程中出现的问题。如果不是由spec脚本引起的错误，请忽略。

{info}

spec脚本：
{spec}
"""


class SpecBot:
    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        base_url = settings.OPENAI_BASE_URL
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = settings.SPECBOT_AI_MODEL

    def repair(self, spec_lines: list, log_lines: list):
        '''
        repair spec file content

        :param spec_lines: content of error spec file
        :type list

        :param log_lines: content of error log
        :type list

        :return
        :type tuple(str, bool, list(str), str)

        '''
        spec = self._preprocess_spec(deepcopy(spec_lines))
        log = self._preprocess_log(log_lines)

        tools = self._prepare_tools()
        messages = self._prepare_messages(spec, log)
        fault_segment = None
        repaired_segment = None

        is_repaired = False
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "repair_spec"}
                }
            )
            tool_calls = response.choices[0].message.tool_calls
            arguments = tool_calls[0].function.arguments
            arguments = json.loads(arguments)
            suggestion = arguments.get("suggestion", None)
            fault_segment = arguments.get("fault_segment", None)
            repaired_segment = arguments.get("repaired_segment", None)

            if suggestion and fault_segment and repaired_segment:
                is_repaired, repaired_spec_lines = repair_spec_impl(
                    deepcopy(spec_lines), fault_segment, repaired_segment
                )
        except Exception as e:
            raise Exception(f'repair call ai server err, [{e}]')

        if is_repaired:
            patch = get_patch(spec_lines, repaired_spec_lines)
        else:
            patch = None
        log_content = save_log(is_repaired,
                               log,
                               suggestion,
                               fault_segment,
                               patch)

        repaired_spec_str = ''.join(repaired_spec_lines)
        return suggestion, is_repaired, repaired_spec_str, log_content

    def repair_pro(self, spec_lines, log_lines, doc_content=None):
        '''
        repair spec file content with doc

        :param spec_lines: content of error spec file
        :type list

        :param log_lines: content of error log
        :type list

        :return
        :type tuple(str, bool, list(str), str)

        '''
        spec = self._preprocess_spec(deepcopy(spec_lines))
        log = self._preprocess_log(log_lines)
        tools = self._prepare_tools_pro()
        fault_segment = None
        repaired_segment = None

        is_repaired = False
        try:
            messages = self._prepare_messages_pro_1(spec, log, doc_content)
            response = self.client.chat.completions.create(
                model=settings.REPAIR_PRO_AI_MODEL, messages=messages
            )
            suggestion = response.choices[0].message.content

            messages = self._prepare_messages_pro_2(spec,
                                                    suggestion,
                                                    doc_content)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "repair_spec_pro"},
                },
            )
            tool_calls = response.choices[0].message.tool_calls
            arguments = tool_calls[0].function.arguments
            arguments = json.loads(arguments)
            fault_segment = arguments.get("fault_segment", None)
            repaired_segment = arguments.get("repaired_segment", None)

            if suggestion and fault_segment and repaired_segment:
                is_repaired, repaired_spec_lines = repair_spec_impl(
                    deepcopy(spec_lines), fault_segment, repaired_segment
                )

        except Exception as e:
            raise Exception(f'repair_pro call ai server err, [{e}]')

        if is_repaired:
            patch = get_patch(spec_lines, repaired_spec_lines)
        else:
            patch = None

        log_content = save_log(is_repaired,
                               log,
                               suggestion,
                               fault_segment,
                               patch)

        repaired_spec_str = ''.join(repaired_spec_lines)
        return suggestion, is_repaired, repaired_spec_str, log_content

    def _prepare_messages(self, spec, log):
        # 准备消息
        messages = []
        if SYSTEM_PROMPT:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append(
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(spec=spec, log=log)
            }
        )
        return messages

    def _prepare_messages_pro_1(self, spec, log, doc):
        messages = []
        if SYSTEM_PROMPT_PRO:
            messages.append({"role": "system", "content": SYSTEM_PROMPT_PRO})
        messages.append(
            {
                "role": "user",
                "content": PROMPT_TEMPLATE_PRO_1.format(spec=spec,
                                                        log=log,
                                                        doc=doc),
            }
        )
        return messages

    def _prepare_messages_pro_2(self, spec, info, doc):
        messages = []
        messages.append(
            {
                "role": "user",
                "content": PROMPT_TEMPLATE_PRO_2.format(spec=spec,
                                                        info=info,
                                                        doc=doc),
            }
        )
        return messages

    def _prepare_tools(self):
        # 准备工具
        return [gen_func_description(repair_spec)]

    def _prepare_tools_pro(self):
        # 准备工具
        return [gen_func_description(repair_spec_pro)]

    def _preprocess_spec(self, lines: list):
        '''
        pre-process spec file content
        '''
        index = 0
        for i in range(len(lines)):
            lines[i] = f"{index}: " + lines[i]
            index += 1
        start_index = 0
        for i in range(len(lines)):
            if "License" in lines[i]:
                start_index = i + 1
                break
            if "BuildRequires" in lines[i]:
                start_index = i
                break
        spec = "".join(lines[start_index:])
        return spec

    def _preprocess_log(self, lines: list):
        '''
        pre-process log file content
        '''
        start_index = 0
        end_index = len(lines)

        for i in range(len(lines) - 1, -1, -1):
            if "Child return code was: 1" in lines[i]:
                end_index = i

            pattern = re.compile(r"^Executing\(%\w+\):")
            if pattern.match(lines[i]):
                start_index = i
                break

        log = "".join(lines[start_index:end_index])

        return log
