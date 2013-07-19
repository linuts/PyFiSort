"""
                    Copyright (C) 2013 Alexander B. Libby

    This PyFiSort is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from shutil import copy2 as copyfile
from shutil import copytree, rmtree
from re import search
from datetime import datetime
import os

class LogCommand():
    '''
    '''
    filename = ""

    @staticmethod
    def logdate():
        '''
        '''
        if not LogCommand.filename == "":
            now = datetime.now()
            now = now.strftime("%Y-%m-%d %H:%M:%S")
            with open(LogCommand.filename, 'a') as data:
                data.write("\nLogged @ {0}\n".format(now))
        else:
            raise Exception("LogCommand.filename not set")

    def __init__(self, logas):
        '''
        '''
        self.note = logas

    def __call__(self, function):
        '''
        '''
        def wrapped(*args):
            '''
            '''
            with open(LogCommand.filename, "a") as data:
                try:
                    output = function(*args)
                except Exception as exc:
                    output = exc
                if not output == None:
                    log = "{0}: {1}\n".format(self.note, output)
                    if log == "{0}: \n".format(self.note):
                        log = ""
                else:
                    log = "{0}\n".format(self.note)
                data.write(log)
                print(log)
            return output
        return wrapped

class PySort():
    '''
    '''

    def __init__(self, file):
        '''
        '''
        io_data = open(file, "r")
        LogCommand.filename = file + ".log"
        LogCommand.logdate()
        lines = []
        for line in io_data.readlines():
            cmds = dict()
            for cmd in line.split(" "):
                cmd = cmd.replace("//", " ")
                cmd = cmd.strip(os.linesep)
                skip_cmd = False
                part_index = 0
                parts = dict()
                for part in cmd.rsplit("::"):
                    if part_index == 0:
                        if not (len(part) > 0 and part.isupper()):
                            skip_cmd = True
                            break
                        else:
                            key = part
                            parts[key] = []
                    else: parts[key] += [part]
                    part_index += 1
                if skip_cmd: break
                cmds.update(parts)
            if len(cmds) > 0 : lines += [cmds]
        io_data.close()
        self.data = tuple(lines)
        self.vars = dict()

    def get_files(self, args, path):
        '''
        '''
        files = []
        try:
            file = path.split("/")[len(path.split("/")) - 1]
            for arg in args:
                if "IS" in self.vars[arg] and "NOT" in self.vars[arg]:
                    for isin in self.vars[arg]["IS"]:
                        if search(isin, file):
                            skip = False
                            for notin in self.vars[arg]["NOT"]:
                                if search(notin, file):
                                    skip = True
                                    break
                            if not skip:
                                files += [path]
                elif "IS" in self.vars[arg]:
                    for var in self.vars[arg]["IS"]:
                        if search(var, file): files += [path]
                elif "NOT" in self.vars[arg]:
                    for var in self.vars[arg]["NOT"]:
                        if not search(var, file): files += [path]
        except KeyError:
            pass
        return files

    def run_cmds(self):
        '''
        Makes commands run in file order.
        '''
        for command in self.data:
            #print(command)
            if "VAR" in command: self.set_vars(command)
            elif "DIR" in command: self.dir(command)
            elif "RUN" in command: self.run(command)
            elif "DELETE" in command: self.delete(command)
            elif "RENAME" in command: self.rename(command)
            elif "MOVE" in command: self.move(command)
            elif "COPY" in command: self.copy(command)

    def set_vars(self, command):
        '''
        '''
        for var in command["VAR"]:
            if not var in self.vars:
                self.vars[var] = dict()
            if "IS" in command:
                if "IS" in self.vars[var]:
                    self.vars[var]["IS"] = self.vars[var]["IS"].union(set(command["IS"]))
                else:
                    self.vars[var]["IS"] = set(command["IS"])
            if "NOT" in command:
                if "NOT" in self.vars[var]:
                    self.vars[var]["NOT"] = self.vars[var]["NOT"].union(set(command["NOT"]))
                else:
                    self.vars[var]["NOT"] = set(command["NOT"])

    @LogCommand("Pwd")
    def dir(self, command):
        '''
        Change the working directory.
        '''
        pwd = ""
        for part in command["DIR"]:
            pwd += part + "/"
        if os.path.isdir(pwd):
            os.chdir(pwd)
        else:
            raise Exception("DirectoryNotFound " + pwd)
        return pwd

    @LogCommand("Running")
    def run(self, command):
        '''
        '''
        output = ""
        rawFrom = set()
        for part in command["FROM"]:
            for file in os.listdir(part):
                if(part[len(part)-1] != "/"):
                    part += "/"
                rawFrom.add(part + file)
        args = set()
        for part in command["RUN"]:
            args.add(part)
        cargs = ""
        try:
            for part in command["ARGS"]:
                cargs += part + " "
                cargs = cargs[0:-1]
        except KeyError:
            cargs = ''
        for folderFrom in rawFrom:
                for file in self.get_files(args, folderFrom):
                    os.popen(file + " " + str(cargs))
                    output += "\n\tfrom:{0} args:{1}".format(file, str(cargs))
        return output

    @LogCommand("Deleted")
    def delete(self, command):
        '''
        '''
        output = ""
        rawFrom = set()
        for part in command["FROTOM"]:
            for file in os.listdir(part):
                if(part[len(part)-1] != "/"):
                    part += "/"
                rawFrom.add(part + file)
        args = set()
        for part in command["DELETE"]:
            args.add(part)
        for folderFrom in rawFrom:
            for file in self.get_files(args, folderFrom):
                try:
                    rmtree(file)
                except OSError:
                    os.remove(file)
                output += "\n\t{0}".format(file)
        return output

    @LogCommand("Copied")
    def copy(self, command):
        '''
        '''
        output = ""
        rawFrom = set()
        for part in command["FROM"]:
            for file in os.listdir(part):
                if(part[len(part)-1] != "/"):
                    part += "/"
                rawFrom.add(part + file)
        args = set()
        for part in command["COPY"]:
            args.add(part)
        rawTo = set()
        for part in command["TO"]:
            if not os.path.isdir(part):
                os.makedirs(part)
            rawTo.add(part)
        for folderFrom in rawFrom:
            for folderTo in rawTo:
                for file in self.get_files(args, folderFrom):
                    try:
                        copytree(file, folderTo)
                    except OSError:
                        num = "-1"
                        filename = file.split("/")[-1]
                        new_filename = "/" + filename
                        while os.path.isfile(folderTo + new_filename):
                            num = str(int(num) + 1)
                            new_filename = "/(" + num  + ")" + filename
                        copyfile(file, folderTo + new_filename)
                        output += "\n\tfrom:{0} to:{1}".format(file, folderTo + new_filename)
        return output

    @LogCommand("Renamed")
    def rename(self, command):
        '''
        '''
        output = ""
        rawFrom = set()
        for part in command["FROM"]:
            for file in os.listdir(part):
                if(part[len(part)-1] != "/"):
                    part += "/"
                rawFrom.add(part + file)
        args = set()
        for part in command["RENAME"]:
            args.add(part)
        for folderFrom in rawFrom:
            for file in self.get_files(args, folderFrom):
                old_filename = file.split("/")[-1].split(".")
                new_filename = ""
                for index, part in enumerate(command["TO"]):
                    if part == "":
                        try:
                            new_filename += old_filename[index]
                        except IndexError:
                            pass
                    else:
                        new_filename += part
                    if not command["TO"][-1] == part:
                        new_filename += "."
                full_dir = ""
                for _dir in folderFrom.split("/")[0:-1]:
                    full_dir += _dir + "/"
                num = "-1"
                out_filename = new_filename
                while os.path.isfile(full_dir + out_filename):
                    num = str(int(num) + 1)
                    out_filename = "(" + num  + ")" + new_filename
                os.rename(folderFrom, full_dir + out_filename)
                output += "\n\tfrom:{0} to:{}".format(folderFrom, full_dir + out_filename)
        return output

    @LogCommand("Moved")
    def move(self, command):
        '''
        '''
        output = ""
        rawFrom = set()
        for part in command["FROM"]:
            for file in os.listdir(part):
                if(part[len(part)-1] != "/"):
                    part += "/"
                rawFrom.add(part + file)
        args = set()
        for part in command["MOVE"]:
            args.add(part)
        rawTo = set()
        for part in command["TO"]:
            if not os.path.isdir(part):
                os.makedirs(part)
            rawTo.add(part)
        for folderFrom in rawFrom:
            for folderTo in rawTo:
                for file in self.get_files(args, folderFrom):
                    try:
                        copytree(file, folderTo)
                    except OSError:
                        num = "-1"
                        filename = file.split("/")[-1]
                        new_filename = "/" + filename
                        while os.path.isfile(folderTo + new_filename):
                            num = str(int(num) + 1)
                            new_filename = "/(" + num  + ")" + filename
                        copyfile(file, folderTo + new_filename)
                        output += "\n\tfrom:{0} to:{1}".format(file, folderTo + new_filename)
            for file in self.get_files(args, folderFrom):
                try:
                    rmtree(file)
                except OSError:
                    os.remove(file)
        return output

if __name__ == "__main__":
    PySort("test.config").run_cmds()
