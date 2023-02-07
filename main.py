from myenv import MyEnv
from threading import Thread
from tornado import ioloop, web
from os import path, listdir
import csv
import json
from datetime import datetime

DATA_DIRECTORY = "data"
SCHEDULES_DIRECTORY = DATA_DIRECTORY+"/schedules"
TEMPLATES_DIRECTORY = "templates"


teacher_schedule_template = open(TEMPLATES_DIRECTORY + "/teacher.html").read()
student_schedule_template = open(TEMPLATES_DIRECTORY + "/student.html").read()
absence_form = open(TEMPLATES_DIRECTORY + "/absence_form.html").read()
substitution_page = open(TEMPLATES_DIRECTORY + "/substitution.html").read()
home_page = open(TEMPLATES_DIRECTORY + "/home.html").read()

wsserver = None
myioloop = None

data = {}


class ScheduleHandler(web.RequestHandler):
    def get(self):
        uri = self.request.uri
        if uri == "/":
            page = home_page
            teachers = ""
            
            for teacher in data['teachers']:
                teachers += '<a href="/teacher/{0}"><div class="teacher">{1}</div></a> '.format(teacher,teacher.capitalize())
            page = page.replace("{{teachers}}", teachers)

            standards = ""
            for std in data['standards']:
                standards += '<a href="/standard/{0}"><div class="std">{0}</div></a> '.format(std,)
            page = page.replace("{{classrooms}}", standards)

            self.write(page)
        elif uri.startswith("/teacher"):
            teacher_name = uri[uri.rindex('/')+1:].lower()
            if teacher_name in data['teachers']:
                self.serve_teacher_schedule(teacher_name)
            else:
                self.write("No teacher with the specified name (%s) exists."%(teacher_name, ))
        elif uri.startswith("/standard"):
            standard = uri[uri.rindex('/')+1:].upper()
            if standard in data['standards']:
                self.serve_student_schedule(standard)
            else:
                self.write("No matching standard (%s) exists."%(standard, ))
        elif uri.startswith("/absence_form"):
            items = ""
            for teacher in data['teachers']:
                items += '<input type="checkbox" name="{0}"/> <label for="{0}">{0}</label><br/>'.format(teacher)
            page = absence_form.replace("{{items}}", items)
            self.write(page)
        elif uri.startswith("/substitution"):
            absent = []
            for teacher in data['teachers']:
                if self.get_argument(teacher,None) != None:
                    absent.append(teacher)
            
            items = ""
            day = datetime.now().strftime("%A").lower()
            if day in ["saturday", "sunday"]:
                day = "monday"
            for teacher in absent:
                if teacher in data['teachers']:
                    items += '<tr>'
                    items += '<td>%s</td>'%(teacher,)
                    classes = data['teachers'][teacher][day]
                    for key in classes:
                        items += '<td>%s</td>'%(classes[key],)
                    items += '</tr>'
            page = substitution_page.replace("{{day}}", day.capitalize())
            page = page.replace("{{date}}", datetime.now().strftime("%d %B, %Y"))
            page = page.replace("{{teachers}}", str(absent))
            page = page.replace("{{items}}", items)

            self.write(page)
        
        else:
            self.redirect("/")

        
    def serve_teacher_schedule(self, teacher_name):
        class_count = 0
        page = teacher_schedule_template
        page = page.replace("{{teacher_name}}", teacher_name.upper())
        page = page.replace("{{class_count}}", str(class_count))
        classes = data['teachers'][teacher_name]
        for day in classes:
            row = classes[day]
            for key in row:
                place_holder = "{{%s_%s}}"%(day,key)
                page = page.replace(place_holder, row[key])
        self.write(page)

    def serve_student_schedule(self, standard):
        page = student_schedule_template
        page = page.replace("{{standard}}", standard.upper())
        classes = data['standards'][standard]
        for day in classes:
            row = classes[day]
            for key in row:
                place_holder = "{{%s_%s}}"%(day,key)
                page = page.replace(place_holder, row[key]['subject'] + "<br/>(" + row[key]['teacher'] + ")")
        self.write(page)


def myws():
    global wsserver, myioloop
    application = web.Application([(r"[\s\S]*", ScheduleHandler),], websocket_ping_interval=10)
    wsserver = application.listen(8888)
    myioloop = ioloop.IOLoop.current()
    eventLoopThread = Thread(target=myioloop.start)
    eventLoopThread.daemon = True
    eventLoopThread.start()

def menu():
    env = MyEnv(".env")
    while True:

        print()
        print("_____________________________________")
        print("|     Schedule Manager               |")
        print("|Manage School Routines With Ease    |")
        print("|____________________________________|")
        print()


        
        print("E. Exit")
        choice = input("Enter your choice: ")
        if choice == "e" or choice == 'E':
            print("stopping the websocket server ...")
            wsserver.stop()
            myioloop.stop()
            env.close()
            print("Good Bye")
            break
        else:
            print("Invalid choice. Please try again!")

def load_data():
    files = listdir(SCHEDULES_DIRECTORY)
    #print(len(files) , " teachers")
    teachers = {}
    standards = {}
    subjects = {}
    for std in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']:
        classes = {}
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            classes[day] = {}
        standards[std]= classes    

    for file in files:
        class_count = 0
        teacher_name = file[:file.index('.')]
        classes = {}
        with open(SCHEDULES_DIRECTORY + "/" + file) as f:
            reader = csv.reader(f)
            header = next(reader)[1:]
            for row in reader:
                day = row[0].lower()
                classes[day] =  {k:v for (k,v) in zip(header,row[1:])}
                for period in classes[day]:
                    std_and_subject = classes[day][period]
                    if len(std_and_subject.strip())>0:
                        std = std_and_subject[:std_and_subject.index(' ')].upper()
                        subject = std_and_subject[std_and_subject.index(' ') + 1:].upper()

                        if subject in subjects:
                            if (teacher_name, std) not in subjects[subject]:
                                subjects[subject].append((std, teacher_name))
                        else:
                            subjects[subject] = [(teacher_name,std)]


                        class_count +=1
                        standards[std][day][period]={'subject':subject, 'teacher': teacher_name}
        teachers[teacher_name] = classes

    
    
    data['teachers'] = teachers
    data['standards'] = standards
    data['subjects'] = subjects

    #print(teachers)
    #print(standards)
    #print(subjects)

if __name__ == '__main__':
    print("Loading the data ...")
    load_data()
    print("Starting server ...")
    myws()
    menu()