bytes_n = 0
last_line_len=0
char_set = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:#.")
def skip_spaces(start, line):
    pos = start
    while pos < len(line) and line[pos] == " ":
        pos += 1
    return pos

def count_tabs(line):
    return skip_spaces(0, line) // 4;

def read_word(start, line):
    pos = start
    res = ""
    while pos < len(line) and line[pos] not in " \n":
        res += line[pos]
        pos += 1
    return res

def read_letters(start, line):
    global char_set
    pos = start
    res = ""
    while pos < len(line) and line[pos] in char_set:
        res += line[pos]
        pos += 1
    return res

def replace_defines(line, defines):
    global char_set
    word = ""
    res = ""
    for s in line:
        if s in char_set:
            word += s
        else:
            res += defines.get(word, word)
            res += s if s != "\r" else ""
            word = ""
    return res

class macro:
    var_positions = []
    def read(file, line):
        global char_set
        variables = dict()
        cursor = 0
        cursor = skip_spaces(cursor, line)
        cursor += len(read_word(cursor, line))
        cursor = skip_spaces(cursor, line)
        wrd = read_word(cursor, line)
        cursor += len(wrd)
        while wrd.strip() != "":
            cursor = skip_spaces(cursor, line)
            wrd = read_word(cursor, line)
            cursor += len(wrd)
            variables[wrd] = len(variables.keys())
            self.var_positions.append([])
        res = ""
        line = file.readline();
        char_n = 0
        while count_tabs(line) != 0:
            word = ""
            for s in line[4:]:
                if s in char_set:
                    wrd += s
                else:
                    if wrd in variables.keys():
                        self.var_positions[variables[wrd]].append(char_n)
                    else:
                        res += wrd + s
                    wrd = ""
                char_n += 1
            res += wrd
            line = file.readline();
        return res, line        

def read_macro(file):
    res = ""
    line = file.readline();
    while count_tabs(line) != 0:
        res += line[4:]
        line = file.readline();
    return res, line

def sort_key(x):
    return x[2]

def convert_expression(exp, var_name, file, is_jump, jump_loc):
    global bytes_n
    global last_line_len
    result = ""
    operations = []
    #pemdas
    coeffs = {"=": -1000, "!": -1000, "not": -1, "and": -2, "or": -3, "<":0,">":0,"<=":0,">=":0,"==": 0,"===": 0,"!=": 0, "+": 1, "-": 1, "//": 2, "*": 3, "/": 3, "<<":4,">>":4,"|": 4, "&": 5, "^": 5, "**": 6, "func": 8}
    functions = {"min", "max", "sin", "asin", "cos", "acos", "tan", "atan", "rand", "sqrt", "floor", "ceil", "log10", "log", "abs", "noise", "len", "angle", "anglediff", "flip"}
    functions_2_params = {"min", "max", "noise"}
    functions_2_params_stack = []
    cell_read_names = set()
    global char_set
    numbers = []
    reading_number = False
    number = ""
    additional_priority = 0
    prev_number = False
    for s in (exp + " "):
        if s in char_set:
            reading_number = True
            number += s
        elif reading_number:
            reading_number = False
            if number in functions:
                if number in functions_2_params:
                    functions_2_params_stack.append(number)
                else:
                    operations.append((number, len(numbers), coeffs["func"]+additional_priority))
            elif number in coeffs.keys():
                if number == "not":
                    operations.append((number, len(numbers), coeffs[number]+additional_priority))
                else:
                    operations.append((number, len(numbers)-1, coeffs[number]+additional_priority))
            elif number[:4] == "cell" or number[:4] == "bank":
                operations.append((number, len(numbers), coeffs["func"]+additional_priority))
                cell_read_names.add(number)
            else:
                numbers.append(number)
                prev_number = True
            number = ""
        if s not in char_set:
            if s == "-":
                if not prev_number:
                    numbers.append("0")
                    operations.append(("-", len(numbers)-1, coeffs["-"]+additional_priority+6))
                else:
                    operations.append(("-", len(numbers)-1, coeffs["-"]+additional_priority))
            elif s == "(" or s == "[":
                additional_priority += 100
            elif s == ")" or s == "]":
                additional_priority -= 100
            elif s == " ":
                pass
            elif s == ",":
                funct = functions_2_params_stack.pop(-1)
                operations.append((funct, len(numbers)-1, coeffs["func"]+additional_priority - 100))
            elif len(operations) != 0 and (operations[-1][0]+s) in coeffs.keys() and not prev_number:
                operations[-1] = (operations[-1][0]+s, len(numbers)-1, coeffs[operations[-1][0]+s]+additional_priority)
            else:
                operations.append((s, len(numbers)-1, coeffs[s]+additional_priority))
            if s not in ") ":
                prev_number = False
                
    operations_to_names = {"+": "add", "-": "sub", "*": "mul", "/": "div", "//": "idiv", "abs": "mod", "**": "pow", "==": "equal", "!=": "notEqual", "and": "land", "<":"lessThan", "<=": "lessThanEq","===": "strictEqual", ">": "greaterThan", ">=": "greaterThanEq", "<<": "shl", ">>": "shr", "|": "or", "or": "or", "&": "and", "^": "xor", "not": "not", }
    jump_operations = {"!=", "==", "===", "<", "<=", ">", ">="}
    operations.sort(key=sort_key, reverse=True)
    temp_var_count = 0
    temp_var_correspondance = dict()
    for operation in operations:
        is_single_param = (operation[0] in functions and operation[0] not in functions_2_params) or operation[0] == "not" or operation[0] in cell_read_names
        var1 = numbers[operation[1]]
        var2 = numbers[operation[1] + (not is_single_param)]
        
        is_var1_temp = (var1[:4]=="temp")
        is_var2_temp = (var2[:4]=="temp")
        temp_var_name = "temp"+str(temp_var_count)
        if not (is_var1_temp or is_var2_temp):
            temp_var_count += 1
            temp_var_name = "temp"+str(temp_var_count)
        else:
            if is_var1_temp:
                temp_var_name = temp_var_correspondance[var1]
            else:
                temp_var_name = temp_var_correspondance[var2]
            if is_var1_temp:
                var1 = temp_var_correspondance[var1]
                temp_var_correspondance[var1] = temp_var_name
            if is_var2_temp:
                var2 = temp_var_correspondance[var2]
                temp_var_correspondance[var2] = temp_var_name
        temp_var_correspondance[temp_var_name] = temp_var_name
        numbers[operation[1]] = temp_var_name
        if not is_single_param:
            numbers[operation[1] + 1] = temp_var_name
        if operation == operations[-1] and not is_jump:
            temp_var_name = var_name
        if is_jump and operation[0] in jump_operations and operation == operations[-1]:
            upcode = "jump " + str(jump_loc) + " " +  operations_to_names[operation[0]] + " " + var1 + " " + var2 + "\n"
            file.write(upcode)
            last_line_len = len(upcode)
            bytes_n += last_line_len
        elif operation[0] not in cell_read_names:
            upcode = "op " + operations_to_names.get(operation[0], operation[0]) + " " + temp_var_name + " " + var1 + " " + var2 + "\n"
            file.write(upcode)
            last_line_len = len(upcode)
            bytes_n += last_line_len
        else:
            upcode = "read " + temp_var_name + " " + operation[0] + " " + var1 + "\n"
            file.write(upcode)
            last_line_len = len(upcode)
            bytes_n += last_line_len
    n_lines = 0
    if len(operations) == 0:
        if is_jump:
            upcode = "jump " + str(jump_loc) + " always\n"
            file.write(upcode)
            last_line_len = len(upcode)
            bytes_n += last_line_len
        else:
            upcode = "set " + var_name + " " + numbers[0] + "\n"
            file.write(upcode)
            last_line_len = len(upcode)
            bytes_n += last_line_len
    elif is_jump and operations[-1][0] not in jump_operations:
        upcode = "jump " + str(jump_loc) + " equal " + temp_var_name + " 1\n"
        file.write(upcode)
        last_line_len = len(upcode)
        bytes_n += last_line_len
        n_lines += 1
    return max(1, len(operations) + n_lines)
    
    
source_name = "mindustry_asm.txt"
output_name = "asm_test.txt"
source_name = input("file source: ")
if source_name == "gen":
    source_name = "generator.txt"
    output_name = "generator_masm.txt"
elif source_name == "dis":
    source_name = "displayer.txt"
    output_name = "displayer_masm.txt"
elif source_name == "proj":
    source_name = "mindustry_asm.txt"
    output_name = "asm_test.txt"
else:
    output_name = input("file output: ")
source = open(source_name, "r")
output = open(output_name, "w")

macros = {}

line_labels = {}

line_labels_unknown = {}

defines = {}

line = source.readline()
cursor = 0
line_n = 0
while line != "":
    line = replace_defines(line, defines)
    cursor = skip_spaces(0, line)
    wrd = read_letters(cursor, line)
    print(wrd)
    cursor += len(wrd)
    if wrd == "macro":
        cursor = skip_spaces(cursor, line)
        name = read_word(cursor, line)
        cursor += len(name)
        res = read_macro(source)
        macros[name] = (res[0], res.count("\n"))
        line = res[1]
        continue
    elif wrd in macros.keys():
        output.write(macros[wrd][0])
        bytes_n += macros[wrd][0]
        line_n += macros[wrd][1]
    elif len(wrd) != 0 and wrd[0] == ":":
        line_labels[wrd[1:]] = line_n
    elif len(wrd) != 0 and wrd[0] == "#":
        pass
    elif wrd == "jump":
        cursor = skip_spaces(cursor, line)
        location = read_word(cursor, line)
        cursor += len(location)
        if location in line_labels.keys():
            line_position = line_labels[location]
        else:
            line_position = " " * 6
        line_n += convert_expression(line[cursor:].strip(), "jump_var", output, True, line_position)
        if location not in line_labels.keys():
            line_labels_unknown[location] = line_labels_unknown.get(location, []) + [bytes_n - last_line_len + len("jump ") + line_n]
        #output.write("jump " + str(line_labels[location]) + " equal jump_var 1")
    elif wrd[:4] == "cell" or wrd[:4] == "bank":
        cursor = skip_spaces(cursor, line)
        pos1 = cursor + 1
        while line[cursor] !=  "]":
            cursor += 1
        mem_adress = line[pos1:cursor].strip()
        will_convert = (read_letters(0, mem_adress) != mem_adress)
        if will_convert:
            line_n += convert_expression(mem_adress, "mem_adress512", output, False, 0)
        cursor = skip_spaces(cursor + 1, line)
        write_var = line[cursor+1:].strip()
        will_convert2 = (read_letters(0, write_var) != write_var)
        if will_convert2:
            line_n += convert_expression(write_var, "write_var512", output, False, 0)
        command = "write " + (write_var if not will_convert2 else "write_var512") + " " + wrd + " "+(mem_adress if not will_convert else "mem_adress512") + "\n"
        output.write(command)
        bytes_n += len(command)
        line_n += 1
    elif wrd == "define":
        cursor = skip_spaces(cursor, line)
        key = read_word(cursor, line)
        cursor += len(key)
        defines[key] = line[cursor:].strip()
    else:
        cursor = skip_spaces(cursor, line)
        if cursor < len(line) and line[cursor] == "=":
            line_n += convert_expression(line[cursor+1:].strip(), wrd, output, False, 0)
        elif line.strip() != "":
            output.write(line[skip_spaces(0, line):])
            bytes_n += len(line[skip_spaces(0, line):])
            line_n += 1
    line = source.readline()
for label in line_labels_unknown.keys():
    for pos in line_labels_unknown[label]:
        output.seek(pos)
        output.write(str(line_labels[label]))
source.close()
output.close()