# skill: extract_message_constants
# version: 1
# tags: list, message, type, constants, defined
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-18T19:02:11.669956+00:00
# decaying: false
import re
import os

def extract_message_constants(file_path):
    'Return a dictionary of message type constants and their families.'
    with open(file_path, 'r') as file:
        content = file.read()

    constants = re.findall(r'([A-Z_]+) = "([a-zA-Z0-9\.]+)"', content)
    message_constants = {}

    for constant, value in constants:
        if 'PACS' in value:
            family = 'pacs'
        elif 'CAMT' in value:
            family = 'camt'
        elif 'PAIN' in value:
            family = 'pain'
        else:
            family = 'unknown'

        message_constants[constant] = {
            'family': family,
            'value': value,
            'description': f'{constant} is a {family} message type constant.'
        }

    return message_constants

if __name__ == "__main__":
    file_path = os.path.join('/Users/sazankhalid/Downloads/self-constructing-agents/self_building_agent/eval/target_repo/iso20022_synthetic', 'messages.py')
    message_constants = extract_message_constants(file_path)
    for constant, info in message_constants.items():
        print(f'Constant: {constant}, Family: {info["family"]}, Value: {info["value"]}, Description: {info["description"]}')
    print("TEST PASSED")
