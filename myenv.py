class MyEnv:
    def __init__(self, file_name):
        file = open(file_name)
        lines = file.readlines()
        data = {}
        for line in lines:
            line = line.strip()
            if line != "":
                kv = line.split('=')
                data[kv[0]]=kv[1]
        self.data = data
        file.close()
    
    def get(self, key):
        return self.data[key]

    def getAppName(self):
        return self.data['APP_NAME']

    def close(self):
        pass