import pytest
from rlm.parser import parse_lm_output, LMOutput


class TestParser:
    def test_full_output(self):
        raw = "THOUGHT: I should search for the function\nCOMMAND: codesearch \"def hello\"\nANSWER: Found 3 matches"
        output = parse_lm_output(raw)
        
        assert output.thought == "I should search for the function"
        assert output.command == 'codesearch "def hello"'
        assert output.answer == "Found 3 matches"
        assert output.parse_error is None

    def test_partial_output_thought_only(self):
        raw = "THOUGHT: Thinking about this..."
        output = parse_lm_output(raw)
        
        assert output.thought == "Thinking about this..."
        assert output.command is None
        assert output.answer is None
        assert output.parse_error is None

    def test_partial_output_command_none(self):
        raw = "THOUGHT: Not sure what to do\nCOMMAND: NONE"
        output = parse_lm_output(raw)
        
        assert output.command is None

    def test_malformed_multiline_command(self):
        raw = "COMMAND: first line\nsecond line should not be here\nANSWER: done"
        output = parse_lm_output(raw)
        
        assert output.command == "first line"
        assert output.answer == "done"

    def test_empty_input(self):
        output = parse_lm_output("")
        assert output.parse_error == "Empty input"
        assert output.thought is None
        assert output.command is None
        assert output.answer is None

    def test_no_sections(self):
        output = parse_lm_output("random text without sections")
        assert output.parse_error == "No THOUGHT, COMMAND, or ANSWER found"

    def test_whitespace_handling(self):
        raw = "THOUGHT:   too much space   \n\nANSWER:   trim me   "
        output = parse_lm_output(raw)
        
        assert output.thought == "too much space"
        assert output.answer == "trim me"