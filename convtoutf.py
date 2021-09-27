import os
import configparser
from datetime import datetime
import pickle
import logging

# Инициализация структуры ini файла
def createConfig(path):
    """
    Create a config file
    """
    config = configparser.ConfigParser()
    config.add_section("general")
    config.set("general", "pathInputAFTN", "C:\\Users\\user\\Desktop\\aftnin")
    config.set("general", "pathOutput", "out\\")
    config.set("general", "InputCode", "cp866")
    config.set("general", "ProcessFlag", "all") #может быть all или today
    config.set("general", "logLevel", "info")
    with open(path, "w") as config_file:
        config.write(config_file)
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, filename='convAFTN.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
    # если нет файла настроек, то создать и выйти сообщив что создан файл с параметрами по умолчанию
    inifile = "settings.ini"
    if not os.path.exists(inifile):
        strline = "ini file not found! Create " + inifile + " file. Edit this file and run as!"
        createConfig(inifile)
        logging.error(strline)
        exit(1)
    #прочитать параметры инициализации
    config = configparser.ConfigParser()
    config.read(inifile)
    pathAFTN = config.get("general", "pathInputAFTN")
    encodingAFTN = config.get("general", "InputCode")
    pathOut = config.get("general", "pathOutput")
    processFlag = config.get("general", "ProcessFlag")
    if processFlag == "all":
        #обработать все телеграммы в папке
        logging.warning("Converting all files in AFTN folder!")
        for dirs,folder,files in os.walk(pathAFTN):
            for file in files:
                #получить путь до файла и считать данные
                file866Name = os.path.join(dirs,file)
                with open(file866Name, 'r', encoding=encodingAFTN) as file:
                    filedata = file.read()
                # обрабатывать только информационные телеграммы и отбрасывать сервисные
                if filedata.find('ЦХ') == -1 or filedata.find('СЖЦ') == -1:
                    #сформировать новое имя для выходного файла
                    newfileName = file866Name[len(pathAFTN)+1:].replace('\\', '-')
                    #записать сконвертированный файл по указанному пути
                    newfileName = os.path.join(pathOut, newfileName)
                    with open(newfileName, 'w') as utffile:
                        utffile.write(filedata)
                    strline = "Read " + file866Name + " file and save as " + newfileName
                    logging.info(strline)
        #при следующем запуске обрабатывать только текущую дату -  сменить флаг в ini файле
        config.set("general", "ProcessFlag", "today")
        with open(inifile, "w") as config_file:
            config.write(config_file)
        logging.warning("Change ProcessFlag from all to today. On next time read only today telegram!")
    if processFlag == "today":
        #обрабатывать только сегодняшние телеграммы
        currentDate = datetime.now()
        strline =  "Start script with process flag today in " + str(currentDate)
        logging.info(strline)
        pathKey = '-'.join([str(currentDate.year),str(currentDate.month).zfill(2),str(currentDate.day).zfill(2)])
        pathAFTN = os.path.join(pathAFTN,str(currentDate.year), str(currentDate.month).zfill(2), str(currentDate.day).zfill(2))
        #восстановить список конвертированных файлов
        try:
            with open('data.pickle', 'rb') as f_data:
                data_pickle = pickle.load(f_data)
                
        except FileNotFoundError:
            data_pickle = {pathKey:[]}
            logging.warning("Pickle dictionary not found. Create new pickle file")
        #если переход суток - очистить словарь и начать с сегодняшнего дня
        if not data_pickle.get(pathKey):
           data_pickle.clear()
           data_pickle = {pathKey:[]}
           logging.warning("New day! renew pickle file.")
        #print(data_pickle)
        #сканируем папку текущего дня
        for dirs,folder,files in os.walk(pathAFTN):
            for file in files:
                file866Name = os.path.join(dirs,file)
                #преобразовывать только те файлы которые сегодня не преобразовывал
                if file866Name not in data_pickle[pathKey]:
                    data_pickle[pathKey].append(file866Name)
                    with open(file866Name, 'r', encoding=encodingAFTN) as file:
                        filedata = file.read()
                    if filedata.find('ЦХ') == -1 or filedata.find('СЖЦ') == -1:
                        #сформировать новое имя для выходного файла
                        newfileName = file866Name[len(config.get("general", "pathInputAFTN"))+1:].replace('\\', '-')
                        #записать сконвертированный файл по указанному пути
                        newfileName = os.path.join(pathOut, newfileName)
                        with open(newfileName, 'w', encoding='utf-8') as utffile:
                            utffile.write(filedata)
                        strline = "Read " + file866Name + " file and save as " + newfileName
                        logging.info(strline)
            #сохранить список обработаннных файлов
            with open('data.pickle', 'wb') as f_data:
                pickle.dump(data_pickle, f_data)
            logging.info("save pickle file!")
