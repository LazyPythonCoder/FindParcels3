import time
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry, Calendar
from tkinter.messagebox import showinfo, showerror
import sqlite3
import os
import json
import requests
import datetime
import babel.numbers

class Main(tk.Frame):

    def __init__(self,root):
        super().__init__(root)
        self.init_main()
        self.db=db
        self.view_records()
        self.style = ttk.Style()
        self.style.map('Treeview', foreground=self.fixed_map('foreground'), background=self.fixed_map('background'))

    def fixed_map(self, option):
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        return [elm for elm in self.style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]


    def init_main(self):
        toolbar = tk.Frame(bg="#d7d8e0", bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        self.add_img = tk.PhotoImage(file="add.gif")
        bt_open_dialog = tk.Button(toolbar, text="Добавить позицию", command=self.open_dialog, bg="#d7d8e0", bd=0,
                                   compound=tk.TOP, image=self.add_img)
        bt_open_dialog.pack(side=tk.LEFT)

        self.update_img = tk.PhotoImage(file='update.gif')
        btn_edit_dialog = tk.Button(toolbar, text='Редактировать', bg='#d7d8e0', bd=0, image=self.update_img,
                                    compound=tk.TOP, command=self.open_update_dialog)
        btn_edit_dialog.pack(side=tk.LEFT)

        self.delete_img = tk.PhotoImage(file='delete.gif')
        btn_delete = tk.Button(toolbar, text='Удалить позицию', bg='#d7d8e0', bd=0, image=self.delete_img,
                               compound=tk.TOP, command=self.delete_records)
        btn_delete.pack(side=tk.LEFT)

        self.mail_img = tk.PhotoImage(file='pochta.gif')
        btn_mail = tk.Button(toolbar, text='Отследить посылку', bg='#d7d8e0', bd=0, image=self.mail_img,
                             compound=tk.TOP, command=self.mail_check_show)
        btn_mail.pack(side=tk.LEFT)

        self.search_img = tk.PhotoImage(file='search.gif')
        btn_search = tk.Button(toolbar, text='Поиск', bg='#d7d8e0', bd=0, image=self.search_img,
                               compound=tk.TOP, command=self.open_search_dialog)
        btn_search.pack(side=tk.LEFT)

        self.refresh_img = tk.PhotoImage(file='refresh.gif')
        btn_refresh = tk.Button(toolbar, text='Обновить', bg='#d7d8e0', bd=0, image=self.refresh_img,
                                compound=tk.TOP, command=self.view_records)
        btn_refresh.pack(side=tk.LEFT)

        self.tree = ttk.Treeview(self, columns=("data_of_order", "treck", "description", "info_mail", "parcel_recieved"), height = 15, show = "headings")
        self.tree.column("data_of_order", width = 100, anchor = tk.CENTER)
        self.tree.column("treck", width = 150, anchor = tk.CENTER)
        self.tree.column("description", width=400, anchor=tk.CENTER)
        self.tree.column("info_mail", width=400, anchor=tk.CENTER)
        self.tree.column("parcel_recieved", width=120, anchor=tk.CENTER)

        self.tree.heading("data_of_order", text = "Дата заказа")
        self.tree.heading("treck", text = "Номер трека")
        self.tree.heading("description", text="Описание заказа")
        self.tree.heading("info_mail", text="Статус посылки")
        self.tree.heading("parcel_recieved", text="Статус получения")
        self.tree.pack()
        self.tree.bind('<<TreeviewSelect>>', self.item_selected)

    def item_selected(self, event):
        global record
        for selected_item in self.tree.selection():
            item = self.tree.item(selected_item)
            record = item['values']
        return record

    def records(self,data_of_order, treck, description, info_mail="Нет данных", parcel_recieved="False"):
        self.db.insert_data(data_of_order, treck, description, info_mail, parcel_recieved)
        self.view_records()

    def update_record(self, data_of_order, treck, description, info_mail="Нет данных", parcel_recieved="False", flag=False):
        self.db.c.execute('''UPDATE parcels SET data_of_order=?, treck=?, description=?, info_mail=?, parcel_recieved=? WHERE treck=?''',
                          (data_of_order, treck, description, info_mail, parcel_recieved, self.tree.set(self.tree.selection()[0], '#2'),))
        self.db.conn.commit()
        self.view_records( treck, flag)

    def open_dialog(self):
        Child()

    def open_update_dialog(self):
        Update()

    def open_search_dialog(self):
        Search()

    def delete_records(self):
        for selection_item in self.tree.selection():
            self.db.c.execute('''DELETE FROM parcels WHERE treck=?''', [self.tree.set(selection_item, '#2')])
            self.db.conn.commit()
        self.view_records()

    def view_records(self, treck="", flag=False):
        self.db.c.execute('''SELECT * FROM parcels''')
        [self.tree.delete(i) for i in self.tree.get_children()]
        for row in self.db.c.fetchall():
            if flag and row[1]==treck:
                print(row[1])
                self.tree.insert('', 'end', values=row, tags=("new"))
            else:
                self.tree.insert('', 'end', values=row, tags=("old"))
        # [self.tree.insert('', 'end', values=row, tags=("old")) for row in self.db.c.fetchall()]

        self.tree.tag_configure("new", foreground="green", background="white")
        self.tree.tag_configure("old", foreground="black", background="white")
    def search_records(self, treck):
        treck = ('%'+treck+'%',)
        self.db.c.execute('''SELECT * FROM parcels WHERE treck LIKE ?''', treck)
        [self.tree.delete(i) for i in self.tree.get_children()]
        [self.tree.insert('', 'end', values=row) for row in self.db.c.fetchall()]

    def get_carrier(self, treck_number):
        carrier="Перевозчик не найден"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "X-Api-Key": "1799fa40855d01e4ec00b4742be8bbda",
            "Content-Type": "application/json"
        }
        if len(treck_number) != 0:
            url_carrier = "https://moyaposylka.ru/api/v1/carriers/" + treck_number
            req = requests.get(url_carrier, headers=headers)
            src = req.text
            if len(src) > 2:
                res_dict = json.loads(src, encoding="utf-8")
                res_dict = list(res_dict)[0]
                carrier = res_dict["code"]
                print(carrier)
                return carrier
            else:
                return carrier
        else:
            return carrier

    def set_treck(self, treck_number):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "X-Api-Key": "1799fa40855d01e4ec00b4742be8bbda",
            "Content-Type": "application/json"
        }
        url_post_trek = " https://moyaposylka.ru/api/v1/trackers/" + self.get_carrier(treck_number) + "/" + treck_number
        req = requests.post(url_post_trek, headers=headers)
        src = req.text
        print("Ответ сайта на постановку трека на поиск")
        print(src)
        return src

    def mail_check(self, treck_number):
        mail_events = {}
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "X-Api-Key": "1799fa40855d01e4ec00b4742be8bbda",
            "Content-Type": "application/json"
        }
        carrier = self.get_carrier(treck_number)
        if carrier !="Перевозчик не найден":
            self.set_treck(treck_number)
            time.sleep(3)
            url = "https://moyaposylka.ru/api/v1/trackers/" + self.get_carrier(treck_number) + "/" + treck_number
            print(url)
            req = requests.get(url, headers=headers)
            src = req.text
            res_dict = json.loads(src, encoding="utf-8")
            message = list(res_dict.values())[0]
            if message == 404:
                return mail_events
            else:
                events = res_dict["events"]
                if len(events) > 0:
                     for event in events:
                        try:
                            timestamp = str(event['eventDate'])[:-3]
                            date_oper = datetime.datetime.fromtimestamp(int(timestamp))
                            mail_events[date_oper] = event['operation']
                        except:
                            mail_events[date_oper] = "ИЕРЕГЛИФЫ!!"
                     return mail_events
                else:
                     return mail_events
        else:
            return mail_events

    def mail_check_show(self):
        trek=""
        recieved_events = ["Получено адресатом", "Package received", "Вручено в постамате", "Получено"]
        for selection_item in self.tree.selection():
            data_of_order = self.tree.set(selection_item, '#1')
            trek =  self.tree.set(selection_item, '#2')
            description = self.tree.set(selection_item, '#3')
            info_mail = self.tree.set(selection_item, '#4')
            parcel_recieved = self.tree.set(selection_item, '#5')
            print(info_mail)

        info_window = tk.Toplevel(self)
        info_window.title("Поиск информации...")
        info_window.geometry('400x50')
        info_window.resizable(False, False)
        lbl_info1 = tk.Label(info_window, text="Поиск данных для посылки: " + trek, font="Arial 12")
        lbl_info1.pack()
        lbl_info2 = tk.Label(info_window, text="Ждем-с...", font="Arial 12")
        lbl_info2.pack()
        info_window.update()

        if len(trek) ==0:
            showerror(title='Ошибка', message="Выдилите запись!")
        else:
            mail_answer = self.mail_check(trek)
            if len(mail_answer)==0:
                showinfo(title='Information', message="Посылка не надена")
            else:
                i=0
                info=[]
                opp=[]
                oppstr=[]
                flag=False
                for key, value in sorted(mail_answer.items(), reverse=True):
                    i = i + 1
                    print(i, " ## ", key, " ## ", value)
                    text_str = str(i) + " ## " + str(key) + " ## " + value + "\n"
                    opp_str = str(key) + " ## " + value
                    info.append(text_str)
                    opp.append(mail_answer[key])
                    oppstr.append(opp_str)


                showinfo(title='Information from ' + self.get_carrier(trek), message=info)
                if info_mail !=  oppstr[0]:
                    print("Статус посылки изменился!!!")
                    flag=True
                info_mail = oppstr[0]

                if opp[0] in recieved_events:
                    print("Посылка получена!")
                    parcel_recieved = "True"

                self.update_record(data_of_order, trek, description, info_mail, parcel_recieved, flag)

        info_window.destroy()


class Child(tk.Toplevel):
    def __init__(self):
        super().__init__(root)
        self.init_child()
        self.view = app

    def init_child(self):
        self.title("Добавить трек посылки")
        self.geometry("650x220+400+300")
        self.resizable(False, False)
        label_data_of_order=tk.Label(self, text="Дата заказа:")
        label_data_of_order.place(x=50, y=50)
        label_treck=tk.Label(self, text="Трек код:")
        label_treck.place(x=50, y=80)
        label_description=tk.Label(self, text="Описание посылки:")
        label_description.place(x=50, y=110)

        self.entry_data_of_order=DateEntry(self, date_pattern = 'dd-mm-YYYY')
        self.entry_data_of_order.place(x=180, y=50)

        self.entry_treck=ttk.Entry(self)
        self.entry_treck.place(x=180, y=80)

        self.entry_description=tk.Entry(self)
        self.entry_description.place(x=180, y=110, width=440)

        self.btn_close=ttk.Button(self, text="Закрыть", command=self.destroy)
        self.btn_close.place(x=300, y=170)

        self.btn_add=ttk.Button(self, text="Добавить")
        self.btn_add.place(x=220, y=170)
        self.btn_add.bind('<Button-1>', lambda event: self.view.records(self.entry_data_of_order.get(), self.entry_treck.get(), self.entry_description.get()))
        self.grab_set()
        self.focus_set()

class Update(Child):
    def __init__(self):
        super().__init__()
        self.init_edit()
        self.view=app

    def init_edit(self):
        global record
        print(record)
        self.title("Редактировать данные")
        self.btn_add.destroy()
        btn_edit = ttk.Button(self, text="Редактировать")
        btn_edit.place(x=205, y=170)
        self.entry_data_of_order=ttk.Entry(self)
        self.entry_data_of_order.place(x=180, y=50)
        btn_edit.bind('<Button-1>', lambda event: self.view.update_record(self.entry_data_of_order.get(),
                                                                          self.entry_treck.get(),
                                                                          self.entry_description.get(),
                                                                          record[3],
                                                                          record[4]))
        if len(record)==0:
            showerror(title='Ошибка', message="Выдилите запись!")
            self.destroy()
        else:
            self.entry_data_of_order.insert(0, record[0])
            self.entry_treck.insert(0, record[1])
            self.entry_description.insert(0, record[2])


class Search(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.init_search()
        self.view = app

    def init_search(self):
        self.title('Поиск трека')
        self.geometry('300x100+400+300')
        self.resizable(False, False)

        label_search = tk.Label(self, text='Поиск по треку')
        label_search.place(x=50, y=20)

        self.entry_search = ttk.Entry(self)
        self.entry_search.place(x=105, y=20, width=150)

        btn_cancel = ttk.Button(self, text='Закрыть', command=self.destroy)
        btn_cancel.place(x=185, y=50)

        btn_search = ttk.Button(self, text='Поиск')
        btn_search.place(x=105, y=50)
        btn_search.bind('<Button-1>', lambda event: self.view.search_records(self.entry_search.get()))
        btn_search.bind('<Button-1>', lambda event: self.destroy(), add='+')




class DB():
    def __init__(self):
        self.conn = sqlite3.connect("parcels.db")
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS parcels (data_of_order DATE, treck PRIMARY KEY UNIQUE, description TEXT, info_mail TEXT DEFAULT [Нет данных], parcel_recieved BOOLEAN DEFAULT (False))''')
        self.conn.commit()

    def insert_data(self, data_of_order, treck, description, info_mail="Нет данных", parcel_recieved="False"):
        self.c.execute('''INSERT INTO parcels(data_of_order, treck, description, info_mail, parcel_recieved) VALUES(?,?,?,?,?)''', (data_of_order, treck, description, info_mail, parcel_recieved))
        self.conn.commit()

record = []
root = tk.Tk()
db=DB()
app = Main(root)
app.pack()
root.title("Мои посылки")
root.geometry("1200x450+300+200")
root.resizable(False,False)
root.mainloop()

if __name__=="main":
    main()

