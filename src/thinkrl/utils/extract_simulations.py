#!/usr/bin/env python3
"""
Script to extract simulations from a JSON file and create a JSONL file
with filtered simulation data (keeping only specific fields and messages).
"""

import json
import sys
import argparse
from pathlib import Path


def filter_user_tool_calls(messages):
    """
    Filter out user tool calls and their corresponding tool responses.

    Args:
        messages: List of message dictionaries

    Returns:
        List of filtered messages without user tool calls and tool responses
    """
    # Collect tool call IDs from user messages with tool calls
    tool_call_ids = set()
    for message in messages:
        if (message.get('role') == 'user' and
            message.get('tool_calls') is not None):
            for tool_call in message.get('tool_calls', []):
                tool_call_ids.add(tool_call.get('id'))

    # Filter out user tool calls and tool responses
    filtered_messages = []
    for message in messages:
        # Skip user messages with tool calls
        if (message.get('role') == 'user' and
            message.get('tool_calls') is not None):
            continue

        # Skip tool responses matching collected IDs
        if (message.get('role') == 'tool' and
            message.get('id') in tool_call_ids):
            continue

        filtered_messages.append(message)

    return filtered_messages


def extract_simulations(input_file: str, output_file: str = None):
    """
    Extract simulations from input JSON file and create filtered JSON output.

    Args:
        input_file: Path to input JSON file
        output_file: Path to output file (optional, defaults to input_file_rollouts_only.json)
    """
    input_path = Path(input_file)

    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_rollouts_only.json"
    else:
        output_file = Path(output_file)

    try:
        # Read the input JSON file
        with open(input_path, 'r') as f:
            data = json.load(f)

        # Extract simulations array
        simulations = data.get('simulations', [])

        # Create JSON output with metadata
        output_data = {
            'timestamp': data.get('timestamp'),
            'info': data.get('info'),
            'simulations': []
        }

        for simulation in simulations:
            # Keep only specific fields (lines 142-147 equivalent)
            filtered_sim = {
                'id': simulation.get('id'),
                'task_id': simulation.get('task_id'),
                'timestamp': simulation.get('timestamp'),
                'start_time': simulation.get('start_time'),
                'end_time': simulation.get('end_time'),
                'duration': simulation.get('duration'),
                'messages': filter_user_tool_calls(simulation.get('messages', []))
            }
            output_data['simulations'].append(filtered_sim)

        # Write as pretty-printed JSON
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Extracted {len(simulations)} simulations to {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Extract simulations to JSON format')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('-o', '--output', help='Output file path (optional)')

    args = parser.parse_args()
    extract_simulations(args.input_file, args.output)


if __name__ == '__main__':
    main()