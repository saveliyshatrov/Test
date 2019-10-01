import os
import json
import threading
import sys
import ftplib

#Чтобы красить текст в консоли
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#Класс с методами
class Files(object):

    def __init__(self, url_from = None, url_to = None):
        self.url_from = url_from
        self.url_to = url_to

    #Чтобы распарсить Файл JSON
    def ParseJSON(self, PathToJSON):
        with open(PathToJSON, "r") as read_file:
            data = json.load(read_file)

        List = []
        LogIn = []
        
        try:
            for i in range(len(data['files'])):
                List.append(Files(data['files'][i]['from'], data['files'][i]['to']))

            LogIn.append(data['forms']['host'])
            LogIn.append(data['forms']['username'])
            LogIn.append(data['forms']['password'])
        except KeyError:
            print(Colors.FAIL + 'Error with JSON file' + Colors.ENDC)
            
        return List, LogIn

    #Передача на FTP сервер
    def TransferFiles(self, PathToJSON):

        value_from = []
        value_to = []

        List, LogIn = self.ParseJSON(PathToJSON)

        #Проверка хоста, логина и пароля на существование
        for i, log in zip(["host", "username", "password"], LogIn):
            if log == "":
                print(Colors.FAIL + 'error with ' + i + Colors.ENDC)
                sys.exit()


        try:
            ftp = ftplib.FTP(host = LogIn[0], user = LogIn[1], passwd = LogIn[2])
            print(Colors.OKGREEN + Colors.BOLD +'Connected successfully' + Colors.ENDC)
        except Exception:
            print(Colors.FAIL + "Connection error" + Colors.ENDC)
            sys.exit()

        array = [List, ftp]

        thread_to   = threading.Thread(target= self.CheckPathOnFTP,      args=(array, value_to))
        thread_from = threading.Thread(target= self.CheckPathOnComputer, args=(List, value_from))

        thread_from.start()
        thread_to.start()

        thread_from.join()
        thread_to.join()

        for i in range(len(List)):
            if value_from[i] == value_to[i] == True:
                filename, file_extension = self.PathLeaf(List[i].url_from)

                if file_extension == '.txt' or file_extension == '.html' or file_extension == '.rst':
                    ftp.storlines('STOR ' + List[i].url_to + '/' + filename + file_extension, open(List[i].url_from,'rb'))
                    print(Colors.OKBLUE + 'File from path ' + List[i].url_from + ' was successfully transfered to ' + List[i].url_to + Colors.ENDC)
                else:
                    ftp.storbinary('STOR ' + List[i].url_to + '/' + filename + file_extension, open(List[i].url_from,'rb'))
                    print(Colors.OKBLUE + 'File from path ' + List[i].url_from + ' was successfully transfered to ' + List[i].url_to + Colors.ENDC)
            else:
                if value_from[i] == False:
                    print(Colors.FAIL + 'File was not transfered because path ' + '"' + List[i].url_from + '"' + ' on computer does not exist' + Colors.ENDC)
                if value_to[i] == False:
                    print(Colors.FAIL + 'File was not transfered because path ' + '"' + List[i].url_to + '"' + ' on server does not exist' + Colors.ENDC)
    
    #чтобы получить расширение файла и отделить название файла от пути
    def PathLeaf(self, path):
        filename = os.path.basename(path)
        a, file_extension = os.path.splitext(path)
        return filename, file_extension
    
    #Проверка пути на компьютере
    def CheckPathOnComputer(self, List, ListOfBools):
        for i in range(len(List)):
            if os.path.exists(List[i].url_from) == False:
                ListOfBools.append(False)
            else:
                ListOfBools.append(True)
        return ListOfBools
    
    #проверка пути на сервере
    def CheckPathOnFTP(self, array, ListOfBools):
        List = array[0]
        ftp = array[1]
        for n in range(len(List)):
            BOOLS = 0
            folders = os.path.normpath(List[n].url_to).split(os.sep)
            for i in range(len(folders)):
                try:
                    ftp.cwd(folders[i])
                except Exception:
                    BOOLS += 1
            
            for i in range(len(folders) - BOOLS):
                ftp.cwd('../')
            
            if BOOLS != 0:
                ListOfBools.append(False)
            else:
                ListOfBools.append(True)
        return ListOfBools

    
#main
PathToJSON = "test.json"
Files().TransferFiles(PathToJSON)