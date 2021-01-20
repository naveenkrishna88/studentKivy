import mysql.connector
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd
from kivy.core.window import Window
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

Window.size = (360, 600)
Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
Window.softinput_mode = 'below_target'

db = mysql.connector.connect(host="brpg5m1l8xcv2q8nabt8-mysql.services.clever-cloud.com", user="ulqlzxo7wrajkyrh",
                             passwd="Jbaa6icE4fSvBqASU5hm", database="brpg5m1l8xcv2q8nabt8")

db_cafe = mysql.connector.connect(host="bpjum1fu8uithbn7fk2n-mysql.services.clever-cloud.com", user="utt8pcxyfysh9vwz",
                                  passwd="fFYduFGCjwhnyLrc1hIy", database="bpjum1fu8uithbn7fk2n")

username_current = ""
hotel_selected = ""


# result = []


class ScreenManagement(ScreenManager):
    pass


class AnimCard(MagicBehavior, MDCard):
    pass


class LogInScreen(Screen):
    def on_pre_enter(self):
        local_cursor = db.cursor()
        local_cursor.execute("select * from login")
        self.result = local_cursor.fetchall()

    def getUsername(self):
        global username_current
        username_current = self.ids.username.text

    def logIn_verify(self):
        if (self.ids.username.text, self.ids.password.text) in self.result:
            self.ids.password.text = ""
            MDApp.get_running_app().root.current = 'hotel'

        else:
            self.ids.animCard_logIn.shake()
            Snackbar(text='Verify your credentials').show()
            return 0


class TopToolbar(MDToolbar):
    def logOut(self):
        MDApp.get_running_app().root.current = 'logIn'


class HotelScreen(Screen):
    global db_cafe
    dish_ordering_list = list()
    dishCount_Order = 0
    totalAmount_Order = 0
    cafe_ordering_currently = ""

    def on_enter(self):
        toast(text="Welcome!")

    def on_pre_enter(self):
        self.cursor = db_cafe.cursor()
        search = "select distinct username from dish"
        self.cursor.execute(search)
        self.hotel_name = list(pd.DataFrame(self.cursor.fetchall())[0])
        self.ids.hotelNames_spinner.values = self.hotel_name

    def dish_filler(self, hotel_selected):
        self.ids.list_dish.clear_widgets()
        search = "select dish, price from dish where username = \"" + hotel_selected + "\" and available = 1"
        self.cursor.execute(search)
        self.dish_available = pd.DataFrame(self.cursor.fetchall()).rename(columns={0: "Dish", 1: "Price"})
        for i in range(len(self.dish_available)):
            l = IconLeftWidget(icon="minus", on_release=self.minus_dish)
            r = IconRightWidget(icon="plus", on_release=self.plus_dish)
            dish_toShow = TwoLineAvatarIconListItem(text=self.dish_available.loc[i, "Dish"],
                                                    secondary_text=str(self.dish_available.loc[i, "Price"]))
            dish_toShow.add_widget(l)
            dish_toShow.add_widget(r)
            self.ids.list_dish.add_widget(dish_toShow)

    def minus_dish(self, instance):
        dish_clicked_toMinus = [widget for widget in instance.walk_reverse()][5]
        try:
            self.dish_ordering_list.remove(dish_clicked_toMinus.text)
            # Snackbar(text=dish_clicked_toMinus.text + " has been removed from cart").show()
            # print(dish_clicked_toMinus.text,int(self.dish_available.query('Dish == @dish_clicked_toMinus.text')['Price']))
            self.dishCount_Order -= 1
            self.totalAmount_Order -= int(self.dish_available.query('Dish == @dish_clicked_toMinus.text')['Price'])
            # print(self.dishCount_Order, self.totalAmount_Order)
            self.ids.bottomToolbar.title = str(self.dishCount_Order) + " items | \u20B9" + str(self.totalAmount_Order)

        except ValueError:
            pass

    def plus_dish(self, instance):
        self.cafe_ordering_currently = self.ids.hotelNames_spinner.text if self.cafe_ordering_currently == "" else self.cafe_ordering_currently
        # print(self.cafe_ordering_currently, self.ids.hotelNames_spinner.text)
        if self.cafe_ordering_currently == self.ids.hotelNames_spinner.text:
            dish_clicked_toPlus = [widget for widget in instance.walk_reverse()][8]
            self.dish_ordering_list.append(dish_clicked_toPlus.text)
            # Snackbar(text=dish_clicked_toPlus.text + " has been added to cart").show()
            # print(dish_clicked_toPlus.text, int(self.dish_available.query('Dish == @dish_clicked_toPlus.text')['Price']))
            self.dishCount_Order += 1
            self.totalAmount_Order += int(self.dish_available.query('Dish == @dish_clicked_toPlus.text')['Price'])
            # print(self.dishCount_Order, self.totalAmount_Order)
            self.ids.bottomToolbar.title = str(self.dishCount_Order) + " items | \u20B9" + str(self.totalAmount_Order)

        else:
            self.dialog = MDDialog(
                title="Replace cart item?",
                text="Your cart has items from " + self.cafe_ordering_currently + ". Do you wish to replace it?",
                buttons=[
                    MDFlatButton(text="NO", on_release=self.dialogResponse),
                    MDFlatButton(text="YES", on_release=self.dialogResponse),
                ],
                size_hint_x = 0.75
            )
            self.dialog.open()

    def dialogResponse(self, responseVal):
        if responseVal.text == "YES":
            self.dish_ordering_list = list()
            self.dishCount_Order = 0
            self.totalAmount_Order = 0
            self.cafe_ordering_currently = ""
            self.ids.bottomToolbar.title = ""
            self.dialog.dismiss()
        else:
            self.dialog.dismiss()

    def verifyOrders_bottom(self):
        orders__frequency_table = {i: self.dish_ordering_list.count(i) for i in self.dish_ordering_list}
        print(orders__frequency_table)


class studentApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = 'BlueGray'


if __name__ == "__main__":
    studentApp().run()