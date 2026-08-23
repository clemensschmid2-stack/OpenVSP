MACRO (TODAY RESULT)
    # Avoid parsing platform- and locale-specific shell command output.
    STRING(TIMESTAMP ${RESULT} "%m/%d/%y")
ENDMACRO (TODAY)
