
import ast

def check_code(code, exercise):
    tree = ast.parse(code)

    flags = {
        "if": False, "else": False, "elif": False,
        "for": False, "while": False,
        "func": False, "print": False, "input": False
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            flags["if"] = True
            if node.orelse:
                if isinstance(node.orelse[0], ast.If):
                    flags["elif"] = True
                else:
                    flags["else"] = True
        if isinstance(node, ast.For):
            flags["for"] = True
        if isinstance(node, ast.While):
            flags["while"] = True
        if isinstance(node, ast.FunctionDef):
            flags["func"] = True
            if exercise.function_name and node.name != exercise.function_name:
                return ["Function name must be " + exercise.function_name]
        if isinstance(node, ast.Call):
            if getattr(node.func, "id", "") == "print":
                flags["print"] = True
            if getattr(node.func, "id", "") == "input":
                flags["input"] = True

    errors = []

    if exercise.require_if and not flags["if"]:
        errors.append("You must use if.")
    if exercise.require_else and not flags["else"]:
        errors.append("You must use else.")
    if not exercise.allow_elif and flags["elif"]:
        errors.append("elif not allowed.")

    if exercise.require_for and not flags["for"]:
        errors.append("for loop required.")
    if exercise.require_while and not flags["while"]:
        errors.append("while loop required.")
    if exercise.forbid_for and flags["for"]:
        errors.append("for loop forbidden.")
    if exercise.forbid_while and flags["while"]:
        errors.append("while loop forbidden.")

    if exercise.require_function and not flags["func"]:
        errors.append("Function required.")
    if exercise.function_name and not flags["func"]:
        errors.append(f"Function '{exercise.function_name}' required.")

    if exercise.require_print and not flags["print"]:
        errors.append("print() required.")
    if exercise.forbid_print and flags["print"]:
        errors.append("print() forbidden.")

    if exercise.require_input and not flags["input"]:
        errors.append("input() required.")

    return errors
