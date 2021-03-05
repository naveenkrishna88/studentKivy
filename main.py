import mysql.connector
import pandas as pd
from random import randint
from datetime import datetime, date
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivymd.uix.behaviors.magic_behavior import MagicBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget, TwoLineListItem, ThreeLineListItem
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.gridlayout import MDGridLayout
from kivy.base import EventLoop
from kivymd.uix.picker import MDTimePicker
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelTwoLine


Window.size = (360, 600)
Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_expo'}
Window.softinput_mode = 'below_target'

db = mysql.connector.connect(host="btyjrjkqioozicbjpsyz-mysql.services.clever-cloud.com", user="utt8pcxyfysh9vwz",passwd="fFYduFGCjwhnyLrc1hIy", database="btyjrjkqioozicbjpsyz", autocommit = True)

username_current = ""


class ScreenManagement(ScreenManager):
    pass


class AnimCard(MagicBehavior, MDCard):
    pass


class LogInScreen(Screen):
    def on_pre_enter(self):
        db.cmd_reset_connection()
        local_cursor = db.cursor()
        local_cursor.execute("select * from loginStudent")
        self.result = local_cursor.fetchall()
        local_cursor.close()


    def logIn_verify(self):
        if (self.ids.username.text, self.ids.password.text) in self.result:
            self.ids.password.text = ""
            MDApp.get_running_app().root.ids.master.current = 'hotel'


        else:
            self.ids.animCard_logIn.shake()
            Snackbar(text='Verify your credentials').show()
            return 0

    def on_leave(self):
        global username_current

        username_current = self.ids.username.text
        toast(text="Welcome!")


class TopToolbar(MDToolbar):
    global username_current

    def openNavigationDraw(self):
        MDApp.get_running_app().root.ids.navDrawLbl.text = "  Welcome " + username_current + "!"
        MDApp.get_running_app().root.ids.nav_drawer.set_state("open")


class NavDrawer(MDNavigationDrawer):

    def goToHome(self):
        MDApp.get_running_app().root.ids.nav_drawer.set_state("close")
        MDApp.get_running_app().root.ids.master.current = 'hotel'

    def logOut(self):
        MDApp.get_running_app().root.ids.nav_drawer.set_state("close")
        MDApp.get_running_app().root.ids.master.current = 'logIn'



class previousOrderScreen(Screen):

    global username_current

    def on_pre_enter(self):
        db.cmd_reset_connection()
        MDApp.get_running_app().root.ids.nav_drawer.set_state("close")

        try:
            cursor = db.cursor()
            previousOrderSQL_statement = "select * from orderDetailsTimeTable where studentUsername = " + "\"" + username_current + "\""
            cursor.execute(previousOrderSQL_statement)
            resultsPreviousOrders = pd.DataFrame(cursor.fetchall()).rename(columns={0: "ordernum", 1: "studentUsername", 2: "hotelName", 3: "timeTakeAway", 4: "totalPay", 5: "orderStatus"}).sort_values(by="timeTakeAway",ascending=False).reset_index(drop=True)
            cursor.close()


            self.ids.historySummary.clear_widgets()

            for i in range(len(resultsPreviousOrders)):
                expansion = MDExpansionPanel(
                    content = ThreeLineListItem(
                        text = "Code :  " + (resultsPreviousOrders.loc[i,"ordernum"][:5] if resultsPreviousOrders.loc[i, "orderStatus"] == 1 else "*****"),
                        secondary_text = "Total Amount :  \u20B9 " + str(resultsPreviousOrders.loc[i, "totalPay"]),
                        tertiary_text =  "Order Status :  " + ("Active" if resultsPreviousOrders.loc[i, "orderStatus"] == 1 else "Completed" if resultsPreviousOrders.loc[i, "orderStatus"] == 0 else "Food not collected. Cancelled"),
                        bg_color = (0,1,0,0.35) if resultsPreviousOrders.loc[i, "orderStatus"] == 1 else (0,0,0,0) if resultsPreviousOrders.loc[i, "orderStatus"] == 0 else (1,0,0,0.5)
                    ),
                    panel_cls = MDExpansionPanelTwoLine(
                        text = resultsPreviousOrders.loc[i, "hotelName"],
                        secondary_text = str(resultsPreviousOrders.loc[i, "timeTakeAway"])
                    )
                )
                self.ids.historySummary.add_widget(expansion)

        except (KeyError, TypeError):
            pass


class HotelScreen(Screen):
    global db

    student_ordering_list = list()
    dishCount_Order = 0
    totalAmount_Order = 0
    hotel_ordering_currently = ""
    dish_available_in_currentSelectedHotel = pd.DataFrame()
    bottomAppID = ""

    def on_pre_enter(self):
        db.cmd_reset_connection()
        HotelScreen.bottomAppID = self.ids.bottomToolbar
        self.cursor = db.cursor()
        search = "select distinct username from dish"
        self.cursor.execute(search)
        self.hotel_names_spinner = list(pd.DataFrame(self.cursor.fetchall())[0])
        self.ids.hotelNames_spinner.values = self.hotel_names_spinner
        self.cursor.close()

    def dish_filler(self, hotel_selected):
        self.ids.list_dish.clear_widgets()
        self.cursor = db.cursor()
        search = "select dish, price from dish where username = \"" + hotel_selected + "\" and available = 1"
        self.cursor.execute(search)
        HotelScreen.dish_available_in_currentSelectedHotel = pd.DataFrame(self.cursor.fetchall()).rename(columns={0: "Dish", 1: "Price"})
        self.cursor.close()
        for i in range(len(HotelScreen.dish_available_in_currentSelectedHotel)):
            l = IconLeftWidget(icon="minus", on_release=self.minus_dish)
            r = IconRightWidget(icon="plus", on_release=self.plus_dish)
            dish_toShow = TwoLineAvatarIconListItem(text=HotelScreen.dish_available_in_currentSelectedHotel.loc[i, "Dish"],
                                                    secondary_text=str('\u20B9') + str(HotelScreen.dish_available_in_currentSelectedHotel.loc[i, "Price"]))
            dish_toShow.add_widget(l)
            dish_toShow.add_widget(r)
            self.ids.list_dish.add_widget(dish_toShow)

    def minus_dish(self, instance):
        dish_clicked_toMinus = [widget for widget in instance.walk_reverse()][5]
        try:
            HotelScreen.student_ordering_list.remove(dish_clicked_toMinus.text)
            HotelScreen.dishCount_Order -= 1
            HotelScreen.totalAmount_Order -= int(HotelScreen.dish_available_in_currentSelectedHotel.query('Dish == @dish_clicked_toMinus.text')['Price'])
            self.ids.bottomToolbar.title = str(HotelScreen.dishCount_Order) + " items | \u20B9" + str(HotelScreen.totalAmount_Order)

        except ValueError:
            pass

    def plus_dish(self, instance):
        HotelScreen.hotel_ordering_currently = self.ids.hotelNames_spinner.text if HotelScreen.hotel_ordering_currently == "" else HotelScreen.hotel_ordering_currently
        if HotelScreen.hotel_ordering_currently == self.ids.hotelNames_spinner.text:
            dish_clicked_toPlus = [widget for widget in instance.walk_reverse()][8]
            HotelScreen.student_ordering_list.append(dish_clicked_toPlus.text)
            HotelScreen.dishCount_Order += 1
            HotelScreen.totalAmount_Order += int(HotelScreen.dish_available_in_currentSelectedHotel.query('Dish == @dish_clicked_toPlus.text')['Price'])
            self.ids.bottomToolbar.title = str(HotelScreen.dishCount_Order) + " items | \u20B9" + str(HotelScreen.totalAmount_Order)

        else:
            self.dialog = MDDialog(
                title="Replace cart item?",
                text="Your cart has items from " + HotelScreen.hotel_ordering_currently + ". Do you wish to replace it?",
                buttons=[
                    MDFlatButton(text="NO", on_release=self.dialogResponse),
                    MDFlatButton(text="YES", on_release=self.dialogResponse),
                ],
                size_hint_x = 0.75
            )
            self.dialog.open()

    def dialogResponse(self, responseVal):
        if responseVal.text == "YES":
            HotelScreen.student_ordering_list = list()
            HotelScreen.dishCount_Order = 0
            HotelScreen.totalAmount_Order = 0
            HotelScreen.hotel_ordering_currently = ""
            self.ids.bottomToolbar.title = ""
            self.dialog.dismiss()
        else:
            self.dialog.dismiss()

    def proceed_to_bill(self):
        if self.ids.bottomToolbar.title != "":
            MDApp.get_running_app().root.ids.master.current = "bill"

    def resetValues(self):
        HotelScreen.student_ordering_list = list()
        HotelScreen.dishCount_Order = 0
        HotelScreen.totalAmount_Order = 0
        HotelScreen.hotel_ordering_currently = ""
        self.dish_available_in_currentSelectedHotel = pd.DataFrame()
        HotelScreen.bottomAppID.title = ""


class BillScreen(Screen):
    global username_current


    def on_enter(self):
        db.cmd_reset_connection()
        self.hotel_obj = HotelScreen()
        self.orders_frequency_table = None
        self.cursor = db.cursor()
        self.ids.bill_hotelName.text = str(self.hotel_obj.hotel_ordering_currently).upper()
        self.orders_frequency_table = {i: self.hotel_obj.student_ordering_list.count(i) for i in self.hotel_obj.student_ordering_list}
        self.ids.toBill_ScrollView.clear_widgets()
        for i in self.orders_frequency_table:
            grid_for_bill_card = MDGridLayout(cols=2, adaptive_height = True)
            billDishName_details = TwoLineListItem(text = str(i), secondary_text = "QTY - " + str(self.orders_frequency_table[i]))
            billDishPrice_details = MDLabel(text = str(int(self.hotel_obj.dish_available_in_currentSelectedHotel.query('Dish == @i')['Price']) * self.orders_frequency_table[i]), halign = 'center')
            grid_for_bill_card.add_widget(billDishName_details)
            grid_for_bill_card.add_widget(billDishPrice_details)
            self.ids.toBill_ScrollView.add_widget(grid_for_bill_card)
        self.ids.billTotalAmountToPay_id.text = "\u20B9 " + str(self.hotel_obj.totalAmount_Order)
        self.cursor.close()

    def show_time_picker(self):
        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_timeFromPicker)
        time_dialog.set_time(datetime.now().time())
        time_dialog.open()

    def get_timeFromPicker(self, instance, time):
        self.time_takeAway = time
        self.ids.bill_timeLbl.text = str(time)
        self.ids.billConfirmBtn.disabled = False

    def placeOrder(self):

        if datetime.combine(date.today(), self.time_takeAway) > datetime.now():

            orderNum = str(randint(10000, 99999)) + str(date.today().year) + str(date.today().month) + str(date.today().day)
            self.cursor = db.cursor()
            placeOrderStatement = "insert into orderDetailsTimeTable(ordernum, studentUsername, hotelName, timeTakeAway, totalPay, orderStatus) values (%s, %s, %s, %s, %s, %s)"
            placeOrderDetails = (orderNum, username_current, self.hotel_obj.hotel_ordering_currently,datetime.combine(date.today(), self.time_takeAway), self.hotel_obj.totalAmount_Order,True)
            self.cursor.execute(placeOrderStatement, placeOrderDetails)

            placeOrderDishTableDetails = []
            for i in self.orders_frequency_table:
                placeOrderDishTableDetails.extend([orderNum, i, self.orders_frequency_table[i]])

            placeOrderDishTableStatement = "insert into orderDishTable(ordernum, dish, quantity) values " + ",".join(
                "(%s, %s, %s)" for dummy in self.orders_frequency_table)

            self.ids.bill_timeLbl.text = "00:00"
            self.ids.billConfirmBtn.disabled = True
            self.cursor.execute(placeOrderDishTableStatement, placeOrderDishTableDetails)
            db.commit()
            self.cursor.close()
            self.hotel_obj.resetValues()
            MDApp.get_running_app().root.ids.master.current = 'hotel'
            Snackbar(text='Order placed').show()
        else:
            Snackbar(text = 'Selecting past time is not valid').show()


class studentApp(MDApp):
    global username_current

    def build(self):
        self.theme_cls.primary_palette = 'BlueGray'
        EventLoop.window.bind(on_keyboard = self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            if MDApp.get_running_app().root.ids.nav_drawer.state == "open":
                MDApp.get_running_app().root.ids.nav_drawer.set_state("close")

            if MDApp.get_running_app().root.ids.master.current == 'hotel':
                MDApp.get_running_app().root.ids.master.current = 'logIn'
            elif MDApp.get_running_app().root.ids.master.current == 'logIn':
                db.close()
                MDApp.get_running_app().stop()
            else:
                MDApp.get_running_app().root.ids.master.current = 'hotel'
            return True


if __name__ == "__main__":
    studentApp().run()
