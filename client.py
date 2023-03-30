import flet as ft
import requests
session = requests.Session()

# server = "http://127.0.0.1:5000/"
server = "https://web-production-037e.up.railway.app/"

class Login(ft.UserControl):
    def __init__(self, controller):
        super().__init__(self)
        self.controller = controller

    def login_handler(self, event):
        ## εδώ στέλνουμε τα στοιχεία του χρήστη στον server και παίρνουμε το session['user'] και το ιστορικό του
        if not self.name.value or not self.passw.value: # δεν έχει συμπληρωθεί ένα από τα πεδία
            self.show_message(None, msg="Πρέπει να δώσετε το όνομα και τον κωδικό σας")
            return
        else:
            data = {"name": self.name.value, "passw": self.passw.value}
            try:
                result = session.post(server + "login", json = data, timeout = 5)
                if result.status_code == 200 and not 'error' in result.json():
                    self.controller.user = self.name.value
                    self.controller.start_questions(result.json()) ## άρχισε το τεστ
                elif 'error' in result.json().keys():
                    self.show_message(None, msg="Λάθος κωδικός - ξαναπροσπαθήστε")
                    return
                else: 
                    self.show_message(None, msg="Αποτυχία σύνδεσης στο python-quiz")
                    return 
            except:
                self.show_message(None, msg="Αποτυχία σύνδεσης στο python-quiz")
                return 

    def show_message(self, event, msg=''):
        self.message.value = msg
        self.message.color = "red"   
        self.update() 
        return
        
    def build(self):
        self.controls = []
        self.controls.append(ft.Text(f"Python-Quiz", color="yellow900", size=30))
        self.controls.append(ft.Text(f'καλωσήρθατε', size=40))
        self.controls.append(ft.Text(f"Κάνετε εγγραφή δίνοντας όνομα/κωδικό ή ξεκινήστε ένα νέο τεστ, αν είστε ήδη γραμμένοι", width='300'))
        self.name = ft.TextField(label='Όνομα:', hint_text="το όνομά σας ...", width='300', on_focus=self.show_message)
        self.controls.append(self.name)
        self.passw = ft.TextField(label="Κωδικός:", password=True, width='300', can_reveal_password=True)
        self.controls.append(self.passw)
        self.controls.append(ft.FilledButton("Ξεκινήστε", on_click= self.login_handler))
        self.message = ft.Text("")
        self.controls.append(self.message)
        return ft.Column(self.controls)

class End(ft.UserControl):
    def __init__(self, controller):
        super().__init__(self)
        self.controller = controller
    def build(self):
        self.controls = []
        self.controls.append(ft.Text(f"Python-Quiz Χρήστης: {self.controller.user}", size=30, color="yellow900"))
        self.controls.append(ft.Text(f'Τελικό σκορ: {100*self.controller.score/len(self.controller.questions_user_controls):.1f}%', size=40))
        self.controls.append(ft.Row([ft.FilledButton("Νέα προσπάθεια", on_click= self.controller.new_game),
                                     ft.OutlinedButton("Έξοδος", icon=ft.icons.EXIT_TO_APP, icon_color="red400", 
                                                       on_click= self.controller.start_login)]))
        return ft.Column(self.controls)

class Quiz(ft.UserControl):
    '''this is a class to run a series of questions and pass back control to the Controller when finished'''
    def __init__(self, controller, label, question, user):
        super().__init__(self)
        self.controller = controller
        self.label = label
        self.question = question
        self.user = user
        self.answered = False

    def submit_handler(self, event):
        if self.submit.text == "Επόμενη ερώτηση": 
            self.controller.update_question()
        if not self.replies.value: 
            self.message.value = f"Παρακαλώ επιλέξτε απάντηση"
            self.message.color = "red"
        else: 
            if self.replies.value == str(self.question["correct"]):
                self.message.value = f"Σωστή απάντηση - συγχαρητήρια!"
                self.message.color = "green"
                self.answered = True
            else: 
                print('---->', type(self.question['correct']), self.question['correct'])
                self.message.value = f"Προσοχή, η σωστή απάντηση είναι : \n{self.question['replies'][str(self.question['correct'])]}"
                self.message.color = "red"
            self.replies.disabled = True
            self.submit.text = "Επόμενη ερώτηση"
        self.update()

    def build(self):
        self.controls = []
        self.controls.append (ft.Text(f"Python-Quiz Χρήστης: {self.user}", size=30, color="yellow900"))
        self.controls.append (ft.Text(f"Ερώτηση αριθμός: {self.label} ({self.question['id']})", size=25))
        self.controls.append (ft.Markdown(f"{self.question['question'].replace('<pre>', '```').replace('</pre>', '```')}",
                                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                            code_style= ft.TextStyle(font_family="Roboto Mono", ),
                                            code_theme="atom-one-dark"))
        self.controls.append ( ft.Text("Απάντηση (επιλέξτε):"))
        replies = [ft.Radio(value= str(x[0]), label= x[1]) for x in self.question['replies'].items()]
        self.replies = ft.RadioGroup(content=ft.Column(replies))
        self.controls.append(self.replies )
        self.submit = ft.FilledButton(f"Υποβολή", on_click=self.submit_handler)
        self.controls.append (self.submit)
        self.message = ft.Text("")
        self.controls.append(self.message)
        return ft.Column(self.controls)
    
class Controller():
    def __init__(self, page):
        self.page = page
        self.start_login(None)

    def start_login(self, event):
        self.user = None
        self.score = 0
        self.questions_user_controls = []
        self.displayed_question = 0
        if self.page.controls: self.page.controls.pop()
        self.page.add(Login(self))

    def start_questions(self, questions=None):
        self.score = 0
        if self.page.controls: self.page.controls.pop() # emtpy page from previous component
        if not questions:
            questions = [{'id': 'Q44', 'question': '**Ποιο το αποτέλεσμα:**\n\n<pre>\ns = ‘123456’\nprint(s[len(s)])\n</pre>\n', 'replies': {1: '‘6’', 2: '‘123456’', 3: '5', 4: 'IndexError', 5: 'Δεν γνωρίζω'}, 'correct': 4},
                 {'id': 'Q39', 'question': 'Τι μάς επιστρέφει η παρακάτω εντολή:\n<pre>\nos.listdir(d)\n</pre>\n', 'replies': {1: 'μας δίνει το όνομα του τρέχοντος φακέλου εργασίας μας', 2: 'μας δίνει μια λίστα με το περιεχόμενο του τρέχοντος φακέλου εργασίας μας', 3: 'μας δίνει μια λίστα με τα ονόματα των υποφακέλων του τρέχοντος φακέλου εργασίας μας', 4: 'μας δίνει το όνομα του φακέλου εγκατάστασης της python στον υπολογιστή μας', 5: 'Δεν γνωρίζω'}, 'correct': 2},
                 {'id': 'Q17', 'question': "Ποιο το αποτέλεσμα:\n<pre>\nfor i in sorted([12, 2, 3, 8, 7]):\n\tif i%3 == 0 : continue\n\telif i%8 == 0 : break\n\telse: print(i, end=' ')\nelse:\n\tprint('end of list')\n</pre>\n", 'replies': {1: '2 3 7 8 12 end of list', 2: '2 7', 3: '2 3 7', 4: '2 3 7 end of list', 5: '2 7 end of list', 6: 'Δεν γνωρίζω'}, 'correct': 2},
                 {'id': 'Q46', 'question': 'Ποιο το αποτέλεσμα;\n<pre>\nli = [5,10,15]\nprint(li.pop(1))\n</pre>\n', 'replies': {1: '[5,15]', 2: '10', 3: '[5,10]', 4: '1', 5: 'Δεν γνωρίζω'}, 'correct': 2},
                 {'id': 'Q1', 'question': "Τι θα τυπώσει το πρόγραμμα;\n<pre>\ndef f():\n\ta = 7\n\tprint(a, end = ' ')\na = 5\nf()\nprint(a, end = ' ')\n</pre>\n", 'replies': {1: '5 5', 2: '7 5', 3: '7 7', 4: 'NameError', 5: 'Δεν γνωρίζω'}, 'correct': 2}
                ]
        for i,q in enumerate(questions):
            print(q)
            label = f"{i+1}/{len(questions)}"
            self.questions_user_controls.append(Quiz(self, label, q, self.user))
        self.update_question()

    def new_game(self, event):
        try:
            result = session.post(server + "newgame", timeout = 5)
            print(result.json())
            if result.status_code == 200:
                self.start_questions(result.json()) ##  pass control to next page
            else:
                self.restart()
        except:
            self.restart()
    
    def restart(self):
        if self.page.controls: self.page.controls.pop() # emtpy page from previous component
        self.page.add(Login(self))

    def update_question(self):
        print(self.displayed_question)
        if 0 <= self.displayed_question < len(self.questions_user_controls):
            if self.page.controls: 
                done_question = self.page.controls.pop()
                if done_question.answered: self.score += 1
            self.page.add(self.questions_user_controls[self.displayed_question])
            self.displayed_question += 1
        else:
            if self.page.controls: done_question = self.page.controls.pop()
            if done_question.answered: self.score += 1
            ### εδώ ολοκληρώνεται το παιχνίδι και επιστρέφουμε τα αποτελέσματα στον server
            data = {"score": self.score/len(self.questions_user_controls)}
            print(data)
            try:
                result = session.post(server + "end", json = data, timeout = 5)
                print(result.json())
                if result.status_code != 200: print("Αποτυχία σύνδεσης στο python-quiz route /end")
            except Exception as error:
                print("Αποτυχία σύνδεσης στο python-quiz route /end", error)
            self.page.add(End(self))

def main(page: ft.Page):
    page.title = "python-quiz"
    page.min_width = 720
    page.window_min_height = 1280
    page.padding=20
    # page.fonts = {
    #     "Roboto Mono": "RobotoMono-VariableFont_wght.ttf",
    # }
    Controller(page)

ft.app(target=main, view=ft.WEB_BROWSER)
