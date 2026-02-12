#!/usr/bin/env python3
"""Estimate token consumption from exported Q Developer chat history."""

import sys
import re

def estimate_tokens(text):
    """Estimate tokens using character count / 4 (common approximation)."""
    return len(text) // 4

def parse_chat_history(filepath):
    """Parse exported chat history and estimate token usage."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by separator
    messages = content.split('\n---\n')
    
    input_tokens = 0
    output_tokens = 0
    user_messages = 0
    assistant_messages = 0
    
    # First message is typically user input
    is_user_turn = True
    
    for msg in messages:
        msg = msg.strip()
        if not msg:
            continue
        
        tokens = estimate_tokens(msg)
        
        if is_user_turn:
            input_tokens += tokens
            user_messages += 1
        else:
            output_tokens += tokens
            assistant_messages += 1
        
        # Alternate between user and assistant
        is_user_turn = not is_user_turn
    
    return {
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python estimate_token_usage.py <chat_history.md>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    result = parse_chat_history(filepath)
    
    print(f"\n{'='*50}")
    print("Q Developer Chat Token Usage Estimate")
    print(f"{'='*50}")
    print(f"User messages:      {result['user_messages']}")
    print(f"Assistant messages: {result['assistant_messages']}")
    print(f"Input tokens:       {result['input_tokens']:,}")
    print(f"Output tokens:      {result['output_tokens']:,}")
    print(f"Total tokens:       {result['total_tokens']:,}")
    print(f"{'='*50}\n")
