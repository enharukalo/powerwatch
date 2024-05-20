from PyQt6 import QtWidgets, uic, QtCore, QtGui
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QInputDialog
from PyQt6.QtCore import QTimer
import mysql.connector, ui_rc
from login_ui import Ui_LoginPage
from register_ui import Ui_RegisterPage
from mainwindow_ui import Ui_MainPage
from adminpanel_ui import Ui_AdminPanel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QGraphicsScene
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import warnings

def create_connection():
    try:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='mysql1234',
            database='energy'
        )
        return db
    except mysql.connector.Error as err:
        print(err)
        return None

class Login(QtWidgets.QMainWindow):
    def __init__(self):
        super(Login, self).__init__()
        self.ui = Ui_LoginPage()
        self.ui.setupUi(self)
        self.ui.btnLogin.clicked.connect(self.handle_login)
        self.ui.btnRegister.clicked.connect(self.open_register)
        self.db = create_connection()
        self.ui.inputUsername.returnPressed.connect(self.handle_login)
        self.ui.inputPassword.returnPressed.connect(self.handle_login)


    def handle_login(self):
        username = self.ui.inputUsername.text()
        password = self.ui.inputPassword.text()
        cursor = self.db.cursor()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'All fields must be filled in.')
            return

        cursor.execute("SELECT * FROM users WHERE UserName = %s AND Password = %s", (username, password))
        result = cursor.fetchone()
        if result:
            self.close()
            user_type = result[-1]  # Get the UserType of the user
            if user_type == 0:  # Normal user
                self.main = Main(username, self.db)
                self.main.show()
            elif user_type == 1:  # Admin user
                reply = QMessageBox.question(self, 'Admin Panel', 'Do you want to open the admin panel?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    self.admin = AdminPanel(username, self.db)
                    self.admin.show()
                else:
                    self.main = Main(username, self.db)
                    self.main.show()
        else:
            QMessageBox.warning(self, 'Error', 'Wrong user or password.')

    def open_register(self):
        self.register = Register(self.db)
        self.register.show()

class Register(QtWidgets.QMainWindow):
    def __init__(self, db):
        super(Register, self).__init__()
        self.ui = Ui_RegisterPage()
        self.ui.setupUi(self)
        self.ui.btnRegister.clicked.connect(self.handle_register)
        self.db = db
        self.ui.inputName.returnPressed.connect(self.handle_register)
        self.ui.inputSurname.returnPressed.connect(self.handle_register)
        self.ui.inputUsername.returnPressed.connect(self.handle_register)
        self.ui.inputPassword.returnPressed.connect(self.handle_register)

    def handle_register(self):
        name = self.ui.inputName.text()
        surname = self.ui.inputSurname.text()
        username = self.ui.inputUsername.text()
        password = self.ui.inputPassword.text()

        if not name or not surname or not username or not password:
            QMessageBox.warning(self, 'Error', 'All fields must be filled in.')
            return

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE UserName = %s", (username,))
        result = cursor.fetchone()

        if result:
            QMessageBox.warning(self, 'Error', 'This username is already taken.')
            return

        cursor.execute("INSERT INTO users (Fname, Lname, UserName, Password) VALUES (%s, %s, %s, %s)", (name, surname, username, password))
        self.db.commit()
        QMessageBox.information(self, 'Success', 'Registered successfully. You can log in now.')
        self.close()

class Main(QtWidgets.QMainWindow):
    def __init__(self, username, db):
        super(Main, self).__init__()
        self.ui = Ui_MainPage()
        self.ui.setupUi(self)
        self.username = username
        self.db = db
        self.userID = self.get_user_id()
        self.load_user_info()
        
        # Set bold font for the labels
        font = QtGui.QFont()
        font.setBold(True)
        self.ui.labelUserInformation.setFont(font)
        self.ui.labelSecuritySettings.setFont(font)
        self.ui.labelUpdatePassword.setFont(font)
        self.ui.labelUpdateUsername.setFont(font)
        self.ui.labelRemoveAccount.setFont(font)
        self.ui.labelRegisteredMeters.setFont(font)
        self.ui.labelAddMeter.setFont(font)
        self.ui.labelRemoveMeter.setFont(font)
        self.ui.labelConnectedDevices.setFont(font)
        self.ui.labelRegisterNewDevice.setFont(font)
        self.ui.labelAvailableDevices.setFont(font)
        self.ui.labelLogConsumption.setFont(font)
        self.ui.labelDeviceConsumptionAnalysis.setFont(font)
        self.ui.labelViewConsumptionHistory.setFont(font)
        self.ui.labelDailyDeviceUsage.setFont(font)
        self.ui.labelHistoricalDeviceUsage.setFont(font)
        self.ui.labelDailyEnergyOverview.setFont(font)
        self.ui.labelMonthlyEnergyOverview.setFont(font)
        self.ui.labelDailyBillSummary.setFont(font)
        self.ui.labelMonthlyBillSummary.setFont(font)

        # Connect the tabWidget signal
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)

        # Connect the buttons to their respective handlers
        self.ui.btnUpdatePassword.clicked.connect(self.update_password)
        self.ui.btnUpdateUsername.clicked.connect(self.update_username)
        self.ui.btnRemoveAccount.clicked.connect(self.remove_account)
        self.ui.btnAddMeter_Add.clicked.connect(self.add_meter)
        self.ui.btnRemoveMeter_Remove.clicked.connect(self.remove_meter)
        self.ui.comboConnectedDevices_MeterID.currentIndexChanged.connect(self.load_connected_devices)
        self.ui.comboDailyDeviceUsage_Meter.currentIndexChanged.connect(self.update_daily_device_usage_date)
        self.ui.comboDailyDeviceUsage_Date.currentIndexChanged.connect(self.draw_daily_device_usage)
        self.ui.comboDailyDeviceUsage_GraphType.currentIndexChanged.connect(self.draw_daily_device_usage)
        self.ui.comboHistoricalDeviceUsage_Meter.currentIndexChanged.connect(self.draw_historical_device_usage)
        self.ui.comboHistoricalDeviceUsage_GraphType.currentIndexChanged.connect(self.draw_historical_device_usage)
        self.ui.comboDailyEnergyOverview_Meter.currentIndexChanged.connect(self.draw_daily_energy_overview)
        self.ui.comboDailyEnergyOverview_GraphType.currentIndexChanged.connect(self.draw_daily_energy_overview)
        self.ui.comboMonthlyEnergyOverview_Meter.currentIndexChanged.connect(self.draw_monthly_energy_overview)
        self.ui.comboMonthlyEnergyOverview_GraphType.currentIndexChanged.connect(self.draw_monthly_energy_overview)
        self.ui.comboDailyBillSummary_Meter.currentIndexChanged.connect(self.draw_daily_bill_summary)
        self.ui.comboDailyBillSummary_GraphType.currentIndexChanged.connect(self.draw_daily_bill_summary)
        self.ui.comboMonthlyBillSummary_Meter.currentIndexChanged.connect(self.draw_monthly_bill_summary)
        self.ui.comboMonthlyBillSummary_GraphType.currentIndexChanged.connect(self.draw_monthly_bill_summary)

        # Connect the returnPressed signals
        self.ui.inputUpdatePassword_CurrentPassword.returnPressed.connect(self.update_password)
        self.ui.inputUpdatePassword_NewPassword.returnPressed.connect(self.update_password)
        self.ui.inputUpdatePassword_ConfirmPassword.returnPressed.connect(self.update_password)
        self.ui.inputUpdateUsername_VerifyPassword.returnPressed.connect(self.update_username)
        self.ui.inputUpdateUsername_NewUsername.returnPressed.connect(self.update_username)
        self.ui.inputUpdateUsername_ConfirmUsername.returnPressed.connect(self.update_username)
        self.ui.inputRemoveAccount_VerifyPassword.returnPressed.connect(self.remove_account)

        # Meter Management
        self.load_registered_meters()
        
        # Device Management
        self.load_connected_devices()
        
        # Consumption Records
        self.load_consumption_records()
        
        # Consumption Analytics and Resize Timer
        self.load_consumption_analytics()
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.redraw_graphs)
        
        # Energy Insights
        self.load_energy_insights()
        
        # Billing Details
        self.load_billing_details()

    def resizeEvent(self, event):
        # Start or restart the timer whenever the window is resized
        self.resize_timer.start(250)  # 500 ms delay

    def redraw_graphs(self):
        # Redraw the graphs
        self.draw_daily_device_usage()
        self.draw_historical_device_usage()
        self.draw_daily_energy_overview()
        self.draw_monthly_energy_overview()
        self.draw_daily_bill_summary()
        self.draw_monthly_bill_summary()
        
    def tab_changed(self, index):
        # Check if the tabConsumptionAnalytics tab is selected
        if self.ui.tabWidget.widget(index) is self.ui.tabConsumptionAnalytics:
            # Redraw the graph
            self.draw_daily_device_usage()
            self.draw_historical_device_usage()
        
        if self.ui.tabWidget.widget(index) is self.ui.tabEnergyInsights:
            # Redraw the graph
            self.draw_daily_energy_overview()
            self.draw_monthly_energy_overview()
            
        if self.ui.tabWidget.widget(index) is self.ui.tabBillingDetails:
            # Redraw the graph
            self.draw_daily_bill_summary()
            self.draw_monthly_bill_summary()

    def get_user_id(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT ID FROM users WHERE UserName = %s", (self.username,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def load_user_info(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE UserName = %s", (self.username,))
        result = cursor.fetchone()

        if result:
            self.ui.labelHeader_FNameandLnameDynamic.setText(f"{result[1]} {result[2]}")
            self.ui.labelUserInfo_UidDynamic.setText(str(result[0]))
            self.ui.labelUserInfo_FnameDynamic.setText(result[1])
            self.ui.labelUserInfo_LnameDynamic.setText(result[2])
            self.ui.labelUserInfo_UsernameDynamic.setText(result[4])

    def update_password(self):
        current_password = self.ui.inputUpdatePassword_CurrentPassword.text()
        new_password = self.ui.inputUpdatePassword_NewPassword.text()
        confirm_password = self.ui.inputUpdatePassword_ConfirmPassword.text()

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE UserName = %s AND Password = %s", (self.username, current_password))
        result = cursor.fetchone()

        if not result:
            QMessageBox.warning(self, 'Error', 'Current password is incorrect.')
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, 'Error', 'New password and confirm password do not match.')
            return

        cursor.execute("UPDATE users SET Password = %s WHERE UserName = %s", (new_password, self.username))
        self.db.commit()
        QMessageBox.information(self, 'Success', 'Password updated successfully.')

    def update_username(self):
        verify_password = self.ui.inputUpdateUsername_VerifyPassword.text()
        new_username = self.ui.inputUpdateUsername_NewUsername.text()
        confirm_username = self.ui.inputUpdateUsername_ConfirmUsername.text()

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE UserName = %s AND Password = %s", (self.username, verify_password))
        result = cursor.fetchone()

        if not result:
            QMessageBox.warning(self, 'Error', 'Password is incorrect.')
            return

        if new_username != confirm_username:
            QMessageBox.warning(self, 'Error', 'New username and confirm username do not match.')
            return

        cursor.execute("SELECT * FROM users WHERE UserName = %s", (new_username,))
        result = cursor.fetchone()

        if result:
            QMessageBox.warning(self, 'Error', 'This username is already taken.')
            return

        cursor.execute("UPDATE users SET UserName = %s WHERE UserName = %s", (new_username, self.username))
        self.db.commit()
        QMessageBox.information(self, 'Success', 'Username updated successfully.')
        self.username = new_username  # Update the current username

    def remove_account(self):
        verify_password = self.ui.inputRemoveAccount_VerifyPassword.text()

        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE UserName = %s AND Password = %s", (self.username, verify_password))
        result = cursor.fetchone()

        if not result:
            QMessageBox.warning(self, 'Error', 'Password is incorrect.')
            return

        cursor.execute("DELETE FROM users WHERE UserName = %s", (self.username,))
        self.db.commit()
        QMessageBox.information(self, 'Success', 'Account removed successfully.')
        self.close()  # Close the main window
    
    def load_registered_meters(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT meter.meterID, meter.type, meter.location 
            FROM meter 
            INNER JOIN usersmeters ON meter.meterID = usersmeters.MeterID 
            WHERE usersmeters.UserID = %s
        """, (self.userID,))
        result = cursor.fetchall()
    
        self.ui.tableRegisteredMeters.setRowCount(0)
    
        for row_number, row_data in enumerate(result):
            self.ui.tableRegisteredMeters.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.ui.tableRegisteredMeters.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))
    
    def add_meter(self):
        meter_type = self.ui.comboAddMeter_MeterType.currentText()
        location = self.ui.comboAddMeter_Location.currentText()
    
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO meter (type, location) VALUES (%s, %s)", (meter_type, location))
        meter_id = cursor.lastrowid
        cursor.execute("INSERT INTO usersmeters (UserID, MeterID) VALUES (%s, %s)", (self.userID, meter_id))
        self.db.commit()
        
        QtWidgets.QMessageBox.information(self, "Success", "Meter added successfully.")
            
        self.load_registered_meters()
        self.load_connected_devices()
    
    def remove_meter(self):
        meter_type = self.ui.comboRemoveMeter_MeterType.currentText()
        location = self.ui.comboRemoveMeter_Location.currentText()

        cursor = self.db.cursor()

        # First, get the ID of the meter to be removed
        cursor.execute("""
            SELECT meter.meterID 
            FROM meter 
            INNER JOIN usersmeters ON meter.meterID = usersmeters.MeterID 
            WHERE usersmeters.UserID = %s AND meter.type = %s AND meter.location = %s
        """, (self.userID, meter_type, location))
        result = cursor.fetchone()
        if result is None:
            QtWidgets.QMessageBox.warning(self, "Error", "No such meter found.")
            return
        meter_id = result[0]

        # Then, delete the devices associated with the meter from the usersdevices table
        cursor.execute("DELETE FROM usersdevices WHERE UserID = %s AND MeterID = %s", (self.userID, meter_id))

        # Then, delete the row from the usersmeters table
        cursor.execute("DELETE FROM usersmeters WHERE UserID = %s AND MeterID = %s", (self.userID, meter_id))

        # Finally, delete the row from the meter table
        cursor.execute("DELETE FROM meter WHERE meterID = %s", (meter_id,))

        self.db.commit()
        
        QtWidgets.QMessageBox.information(self, "Success", "Meter removed.")

        self.load_registered_meters()
        self.load_connected_devices()
        
    def update_user_meters(self):
        # Fetch the meter IDs that the user has
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT meter.meterID 
            FROM usersmeters 
            INNER JOIN meter ON usersmeters.MeterID = meter.meterID
            WHERE usersmeters.UserID = %s
        """ % self.userID)
        meter_ids = [str(item[0]) for item in cursor.fetchall()]

        # Try to disconnect the currentIndexChanged signal
        try:
            self.ui.comboConnectedDevices_MeterID.currentIndexChanged.disconnect()
            self.ui.comboRegisterNewDevice_AssociatedMeterID.currentIndexChanged.disconnect()
        except TypeError:
            pass  # Do nothing if the signal isn't connected to any slot

        # Clear the combo boxes and add the fetched meter IDs
        self.ui.comboConnectedDevices_MeterID.clear()
        self.ui.comboRegisterNewDevice_AssociatedMeterID.clear()
        self.ui.comboConnectedDevices_MeterID.addItems(meter_ids)
        self.ui.comboRegisterNewDevice_AssociatedMeterID.addItems(meter_ids)

        # Reconnect the currentIndexChanged signal
        self.ui.comboConnectedDevices_MeterID.currentIndexChanged.connect(lambda: self.load_connected_devices(False))
        self.ui.comboRegisterNewDevice_AssociatedMeterID.currentIndexChanged.connect(self.load_register_new_device)

        # Manually call load_register_new_device to populate the Device ID combo box
        self.load_register_new_device()
        
    def load_connected_devices(self, update_combo_box=True):
        if update_combo_box:
            self.update_user_meters()
            
        if self.ui.comboConnectedDevices_MeterID.count() == 0:
            return

        # Fetch the devices that are connected to the selected meter
        cursor = self.db.cursor()
        selected_meter_id = self.ui.comboConnectedDevices_MeterID.currentText()
        cursor.execute("""
            SELECT usersdevices.DeviceID, devicedetails.DeviceName, devicedetails.Manufacturer, devicedetails.EnergyRating, devicedetails.`PowerConsumption (per Hour)`
            FROM usersdevices 
            INNER JOIN device ON usersdevices.DeviceID = device.DeviceID
            INNER JOIN devicedetails ON device.DeviceID = devicedetails.DeviceID
            WHERE usersdevices.UserID = %s AND usersdevices.MeterID = %s
        """ % (self.userID, selected_meter_id))
        
        # Check if the user has any devices connected
        if cursor.rowcount == 0:
            return

        # Populate the table with the fetched devices
        self.ui.tableConnectedDevices.setRowCount(0)
        for row_number, row_data in enumerate(cursor):
            self.ui.tableConnectedDevices.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.ui.tableConnectedDevices.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))
                
        self.load_available_devices()
        
    def load_register_new_device(self):
        # Fetch all available device IDs
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT DeviceID 
            FROM device
        """)
        device_ids = [str(item[0]) for item in cursor.fetchall()]
    
        # Clear the Device ID combo box and add the fetched device IDs
        self.ui.comboRegisterNewDevice_DeviceID.clear()
        self.ui.comboRegisterNewDevice_DeviceID.addItems(device_ids)
    
        # Disconnect the clicked signal and connect the register_device_to_meter method to it
        try:
            self.ui.btnRegisterNewDevice.clicked.disconnect()
        except TypeError:
            pass  # Do nothing if the signal isn't connected to any slot
        self.ui.btnRegisterNewDevice.clicked.connect(self.register_device_to_meter)
    
    def register_device_to_meter(self):
        # Get the selected meter ID and device ID
        selected_meter_id = self.ui.comboRegisterNewDevice_AssociatedMeterID.currentText()
        selected_device_id = self.ui.comboRegisterNewDevice_DeviceID.currentText()

        # Check if the device is already associated with the user and meter
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 1 
            FROM usersdevices 
            WHERE UserID = %s AND DeviceID = %s AND MeterID = %s
        """ % (self.userID, selected_device_id, selected_meter_id))
        if cursor.fetchone() is not None:
            # The device is already associated with the user and meter, so show an error message and return
            QtWidgets.QMessageBox.critical(self, "Error", "The device is already associated with the selected meter.")
            return

        # Add the selected device to the meter's connected devices
        cursor.execute("""
            INSERT INTO usersdevices (UserID, DeviceID, MeterID)
            VALUES (%s, %s, %s)
        """ % (self.userID, selected_device_id, selected_meter_id))
        
        self.db.commit()

        # Update the connected devices table
        self.load_connected_devices(True)
    
    def load_available_devices(self):
        cursor = self.db.cursor()
    
        cursor.execute("""
            SELECT device.DeviceID, devicedetails.DeviceName, devicedetails.Manufacturer, devicedetails.EnergyRating, devicedetails.`PowerConsumption (per Hour)`
            FROM device 
            INNER JOIN devicedetails ON device.DeviceID = devicedetails.DeviceID
        """)
        self.ui.tableAvailableDevices.setRowCount(0)
        for row_number, row_data in enumerate(cursor):
            self.ui.tableAvailableDevices.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.ui.tableAvailableDevices.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))
                    
    def load_consumption_records(self):
        # Fetch all meter IDs associated with the current user
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT MeterID 
            FROM usersmeters
            WHERE UserID = %s
        """ % self.userID)
        meter_ids = [str(item[0]) for item in cursor.fetchall()]
    
        # Clear the Meter ID combo boxes and add the fetched meter IDs
        self.ui.comboLogConsumption_MeterID.clear()
        self.ui.comboLogConsumption_MeterID.addItems(meter_ids)
        self.ui.comboViewConsumptionHistory_MeterID.clear()
        self.ui.comboViewConsumptionHistory_MeterID.addItems(meter_ids)
        self.ui.comboDeviceConsumptionAnalysis_MeterID.clear()
        self.ui.comboDeviceConsumptionAnalysis_MeterID.addItems(meter_ids)
    
        # Connect the buttons and combo boxes to their respective methods
        self.ui.btnLogConsumption.clicked.connect(self.log_consumption)
        self.ui.comboViewConsumptionHistory_MeterID.currentIndexChanged.connect(lambda: self.update_date_combo_box(self.ui.comboViewConsumptionHistory_MeterID, self.ui.comboViewConsumptionHistory_Date))
        self.ui.comboViewConsumptionHistory_Date.currentIndexChanged.connect(self.view_consumption_history)
        self.ui.comboLogConsumption_MeterID.currentIndexChanged.connect(self.update_device_combo_box)
        self.ui.comboDeviceConsumptionAnalysis_MeterID.currentIndexChanged.connect(self.update_device_combo_box)
        self.ui.comboDeviceConsumptionAnalysis_DeviceID.currentIndexChanged.connect(self.device_consumption_analysis)
    
        # Auto-fill the View Consumption History and the graph of Device Consumption Analysis
        self.update_date_combo_box(self.ui.comboViewConsumptionHistory_MeterID, self.ui.comboViewConsumptionHistory_Date)
        self.update_device_combo_box()
        self.view_consumption_history()
        self.device_consumption_analysis()
    
    def update_device_combo_box(self):
        # Get the selected meter ID for both frames
        selected_meter_id_log = self.ui.comboLogConsumption_MeterID.currentText()
        selected_meter_id_analysis = self.ui.comboDeviceConsumptionAnalysis_MeterID.currentText()
    
        # Fetch all device IDs from the usages table for the selected meter
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT deviceID 
            FROM usages 
            WHERE userID = %s AND meterID = %s
            ORDER BY deviceID
        """
        cursor.execute(query, (self.userID, selected_meter_id_log))
        device_ids_log = [str(item[0]) for item in cursor.fetchall()]
    
        cursor.execute(query, (self.userID, selected_meter_id_analysis))
        device_ids_analysis = [str(item[0]) for item in cursor.fetchall()]
    
        # Clear the Device ID combo box and add the fetched device IDs
        self.ui.comboLogConsumption_DeviceID.clear()
        self.ui.comboLogConsumption_DeviceID.addItems(device_ids_log)
    
        self.ui.comboDeviceConsumptionAnalysis_DeviceID.clear()
        self.ui.comboDeviceConsumptionAnalysis_DeviceID.addItems(device_ids_analysis)
    
    def update_date_combo_box(self, meter_combo_box, date_combo_box):
        # Get the selected meter ID
        selected_meter_id = meter_combo_box.currentText()
    
        # Fetch all dates from the usages table for the selected meter
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT date 
            FROM usages 
            WHERE userID = %s AND meterID = %s
            ORDER BY date
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        dates = [str(item[0]) for item in cursor.fetchall()]
    
        # Clear the Date combo box and add the fetched dates
        date_combo_box.clear()
        date_combo_box.addItems(dates)
    
    def log_consumption(self):
        # Get the selected meter ID, device ID, date of usage, and consumption duration
        selected_meter_id = self.ui.comboLogConsumption_MeterID.currentText()
        selected_device_id = self.ui.comboLogConsumption_DeviceID.currentText()
        date_of_usage = self.ui.dateLogConsumption_DateOfUsage.date().toString("yyyy-MM-dd")
        consumption_duration = self.ui.doubleSpinBoxLogConsumption_ConsumptionDuration.value()
    
        # Insert the new record into the usages table
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO usages (userID, deviceID, meterID, date, usageAmount)
            VALUES (%s, %s, %s, %s, %s)
        """ % (self.userID, selected_device_id, selected_meter_id, date_of_usage, consumption_duration))
    
        # Update the consumption history table and the consumption analysis graph
        self.view_consumption_history()
        self.device_consumption_analysis()
    
    def view_consumption_history(self):
        # Get the selected meter ID and date
        selected_meter_id = self.ui.comboViewConsumptionHistory_MeterID.currentText()
        selected_date = self.ui.comboViewConsumptionHistory_Date.currentText()

        # If the selected date is not an empty string, fetch the usage records for the selected meter and date
        if selected_date:
            cursor = self.db.cursor()
            query = """
                SELECT deviceID, usageAmount 
                FROM usages 
                WHERE userID = %s AND meterID = %s AND date = %s
            """
            cursor.execute(query, (self.userID, selected_meter_id, selected_date))

            # Update the consumption history table
            self.ui.tableViewConsumptionHistory.setRowCount(0)
            for row_number, row_data in enumerate(cursor):
                self.ui.tableViewConsumptionHistory.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    self.ui.tableViewConsumptionHistory.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))   
    
    def device_consumption_analysis(self):
        # Get the selected meter ID and device ID
        selected_meter_id = self.ui.comboDeviceConsumptionAnalysis_MeterID.currentText()
        selected_device_id = self.ui.comboDeviceConsumptionAnalysis_DeviceID.currentText()

        # Fetch the usage records for the selected meter and device
        cursor = self.db.cursor()
        query = """
            SELECT date, usageAmount 
            FROM usages 
            WHERE userID = %s AND meterID = %s AND deviceID = %s
            ORDER BY date
        """
        cursor.execute(query, (self.userID, selected_meter_id, selected_device_id))

        # Prepare the data for the graph
        dates = []
        usage_amounts = []
        for row in cursor:
            dates.append(row[0])
            usage_amounts.append(row[1])

        self.draw_graph(dates, usage_amounts, 'Line Graph', self.ui.graphicsDeviceConsumptionAnalysis, 'deviceConsumptionAnalysis')
        
    def load_consumption_analytics(self):
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT MeterID 
            FROM usersmeters 
            WHERE UserID = %s
            ORDER BY MeterID
        """
        cursor.execute(query, (self.userID,))
        meter_ids = [str(item[0]) for item in cursor.fetchall()]
        self.ui.comboDailyDeviceUsage_Meter.clear()
        self.ui.comboDailyDeviceUsage_Meter.addItems(meter_ids)
        self.ui.comboHistoricalDeviceUsage_Meter.clear()
        self.ui.comboHistoricalDeviceUsage_Meter.addItems(meter_ids)
    
        # Populate the Graph Type combo boxes
        graph_types = ['Bar Graph', 'Pie Chart']
        self.ui.comboDailyDeviceUsage_GraphType.clear()
        self.ui.comboDailyDeviceUsage_GraphType.addItems(graph_types)
        self.ui.comboHistoricalDeviceUsage_GraphType.clear()
        self.ui.comboHistoricalDeviceUsage_GraphType.addItems(graph_types)
    
        # Update the Date combo box for the selected Meter ID
        self.update_daily_device_usage_date()
            
    def update_daily_device_usage_date(self):
        selected_meter_id = self.ui.comboDailyDeviceUsage_Meter.currentText()
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT date 
            FROM usages 
            WHERE userID = %s AND meterID = %s
            ORDER BY date
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        dates = [str(item[0]) for item in cursor.fetchall()]
        self.ui.comboDailyDeviceUsage_Date.clear()
        self.ui.comboDailyDeviceUsage_Date.addItems(dates)

                
    def draw_daily_device_usage(self):
        selected_meter_id = self.ui.comboDailyDeviceUsage_Meter.currentText()
        selected_date = self.ui.comboDailyDeviceUsage_Date.currentText()
        graph_type = self.ui.comboDailyDeviceUsage_GraphType.currentText()
        cursor = self.db.cursor()
    
        # Check if a valid date is selected
        if selected_date:
            query = """
                SELECT devicedetails.DeviceName, SUM(usages.usageAmount) 
                FROM usages 
                JOIN devicedetails ON usages.deviceID = devicedetails.DeviceID
                WHERE usages.userID = %s AND usages.meterID = %s AND usages.date = %s
                GROUP BY usages.deviceID
            """
            cursor.execute(query, (self.userID, selected_meter_id, selected_date))
            data = cursor.fetchall()
            device_names = [item[0] for item in data]
            usage_amounts = [item[1] for item in data]
            self.draw_graph(device_names, usage_amounts, graph_type, self.ui.graphicsDailyDeviceUsage, 'dailyDeviceUsage')
    
    def draw_historical_device_usage(self):
        selected_meter_id = self.ui.comboHistoricalDeviceUsage_Meter.currentText()
        graph_type = self.ui.comboHistoricalDeviceUsage_GraphType.currentText()
        cursor = self.db.cursor()
        query = """
            SELECT devicedetails.DeviceName, SUM(usages.usageAmount) 
            FROM usages 
            JOIN devicedetails ON usages.deviceID = devicedetails.DeviceID
            WHERE usages.userID = %s AND usages.meterID = %s
            GROUP BY usages.deviceID
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        data = cursor.fetchall()
        device_names = [item[0] for item in data]
        usage_amounts = [item[1] for item in data]
        self.draw_graph(device_names, usage_amounts, graph_type, self.ui.graphicsHistoricalDeviceUsage, 'historicalDeviceUsage')

    def load_energy_insights(self):
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT MeterID 
            FROM usersmeters 
            WHERE UserID = %s
            ORDER BY MeterID
        """
        cursor.execute(query, (self.userID,))
        meter_ids = [str(item[0]) for item in cursor.fetchall()]
        self.ui.comboDailyEnergyOverview_Meter.clear()
        self.ui.comboDailyEnergyOverview_Meter.addItems(meter_ids)
        self.ui.comboMonthlyEnergyOverview_Meter.clear()
        self.ui.comboMonthlyEnergyOverview_Meter.addItems(meter_ids)
    
    def draw_daily_energy_overview(self):
        selected_meter_id = self.ui.comboDailyEnergyOverview_Meter.currentText()
        graph_type = self.ui.comboDailyEnergyOverview_GraphType.currentText()
        cursor = self.db.cursor()
    
        query = """
            SELECT DATE(usages.date), SUM(usages.usageAmount) 
            FROM usages 
            WHERE usages.userID = %s AND usages.meterID = %s
            GROUP BY DATE(usages.date)
            ORDER BY DATE(usages.date)
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        data = cursor.fetchall()
        dates = [item[0] for item in data]
        usage_amounts = [item[1] for item in data]
        self.draw_graph(dates, usage_amounts, graph_type, self.ui.graphicsDailyEnergyOverview, 'dailyEnergyOverview')
    
        # Calculate the next day prediction
        query = """
            SELECT AVG(usageAmount) 
            FROM (
                SELECT SUM(usages.usageAmount) as usageAmount
                FROM usages 
                WHERE usages.userID = %s AND usages.meterID = %s AND DAYOFWEEK(usages.date) = DAYOFWEEK(CURDATE())
                GROUP BY DATE(usages.date)
            ) as subquery
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        prediction = cursor.fetchone()[0]
        # Check if the prediction is None
        if prediction is None:
            self.ui.labelDailyEnergyOverviewPrediction.setText("No usage data available for prediction.")
        else:
            self.ui.labelDailyEnergyOverviewPrediction.setText(f"Next Day Prediction: {prediction:.2f}")
    def draw_monthly_energy_overview(self):
        selected_meter_id = self.ui.comboMonthlyEnergyOverview_Meter.currentText()
        graph_type = self.ui.comboMonthlyEnergyOverview_GraphType.currentText()
        cursor = self.db.cursor()
    
        query = """
            SELECT DATE_FORMAT(usages.date, '%Y-%m'), SUM(usages.usageAmount) 
            FROM usages 
            WHERE usages.userID = %s AND usages.meterID = %s
            GROUP BY DATE_FORMAT(usages.date, '%Y-%m')
            ORDER BY DATE_FORMAT(usages.date, '%Y-%m')
        """
        cursor.execute(query, (self.userID, selected_meter_id))
        data = cursor.fetchall()
        months = [item[0] for item in data]
        usage_amounts = [item[1] for item in data]
        self.draw_graph(months, usage_amounts, graph_type, self.ui.graphicsMonthlyEnergyOverview, 'monthlyEnergyOverview')
    
    def load_billing_details(self):
        cursor = self.db.cursor()
        query = """
            SELECT DISTINCT MeterID 
            FROM usersmeters 
            WHERE UserID = %s
            ORDER BY MeterID
        """
        cursor.execute(query, (self.userID,))
        meter_ids = [str(item[0]) for item in cursor.fetchall()]
        self.ui.comboDailyBillSummary_Meter.clear()
        self.ui.comboDailyBillSummary_Meter.addItems(meter_ids)
        self.ui.comboMonthlyBillSummary_Meter.clear()
        self.ui.comboMonthlyBillSummary_Meter.addItems(meter_ids)
    
    def draw_daily_bill_summary(self):
        selected_meter_id = self.ui.comboDailyBillSummary_Meter.currentText()
        graph_type = self.ui.comboDailyBillSummary_GraphType.currentText()
        cursor = self.db.cursor()
    
        # Get the meter type
        query = """
            SELECT type 
            FROM meter 
            WHERE meterID = %s
        """
        cursor.execute(query, (selected_meter_id,))
        result = cursor.fetchone()
        if result is None:
            return
        meter_type = result[0]
    
        # Set the tariff based on the meter type
        tariff = 0.00113 if meter_type == 'Home' else 0.00283
    
        # Get the daily usage amounts and calculate the cost
        query = """
            SELECT DATE(usages.date), SUM(usages.usageAmount * devicedetails.`PowerConsumption (per Hour)` * %s) 
            FROM usages 
            JOIN devicedetails ON usages.deviceID = devicedetails.DeviceID
            WHERE usages.userID = %s AND usages.meterID = %s
            GROUP BY DATE(usages.date)
            ORDER BY DATE(usages.date)
        """
        cursor.execute(query, (tariff, self.userID, selected_meter_id))
        data = cursor.fetchall()
        dates = [item[0] for item in data]
        costs = [item[1] for item in data]
    
        # Draw the graph
        self.draw_graph(dates, costs, graph_type, self.ui.graphicsDailyBillSummary, 'dailyBillSummary')
    
    def draw_monthly_bill_summary(self):
        selected_meter_id = self.ui.comboMonthlyBillSummary_Meter.currentText()
        graph_type = self.ui.comboMonthlyBillSummary_GraphType.currentText()
        cursor = self.db.cursor()
    
        # Get the meter type
        query = """
            SELECT type 
            FROM meter 
            WHERE meterID = %s
        """
        cursor.execute(query, (selected_meter_id,))
        result = cursor.fetchone()
        if result is None:
            return
        meter_type = result[0]
    
        # Set the tariff based on the meter type
        tariff = 0.00113 if meter_type == 'Home' else 0.00283
    
        # Get the monthly usage amounts and calculate the cost
        query = """
            SELECT DATE_FORMAT(usages.date, '%Y-%m'), SUM(usages.usageAmount * devicedetails.`PowerConsumption (per Hour)` * %s) 
            FROM usages 
            JOIN devicedetails ON usages.deviceID = devicedetails.DeviceID
            WHERE usages.userID = %s AND usages.meterID = %s
            GROUP BY DATE_FORMAT(usages.date, '%Y-%m')
            ORDER BY DATE_FORMAT(usages.date, '%Y-%m')
        """
        cursor.execute(query, (tariff, self.userID, selected_meter_id))
        data = cursor.fetchall()
        months = [item[0] for item in data]
        costs = [item[1] for item in data]
    
        # Draw the graph
        self.draw_graph(months, costs, graph_type, self.ui.graphicsMonthlyBillSummary, 'monthlyBillSummary')    
    
    def draw_graph(self, labels, values, graph_type, graphics_view, graph_name):
        # Get the size of the frame
        width = graphics_view.frameGeometry().width()
        height = graphics_view.frameGeometry().height()
    
        # Convert the size from pixels to inches for matplotlib
        dpi = 100  # Default DPI in matplotlib
        width_in_inches = width / dpi
        height_in_inches = height / dpi
    
        # Create the figure with the specified size
        figure, ax = plt.subplots(figsize=(width_in_inches, height_in_inches))
    
        # Set the background color of the figure and axes
        figure.patch.set_facecolor('#111010')
        ax.set_facecolor('#111010')
    
        # Set the color of the labels and text to white
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.tick_params(colors='white')
        
        # Set the border color to white
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
    
        if graph_type == 'Bar Graph' and (graph_name == 'dailyDeviceUsage' or graph_name == 'historicalDeviceUsage'):
            ax.barh(labels, values, color='#facc10')  # Use barh for horizontal bars
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", UserWarning)
                    plt.tight_layout()  # Adjust the layout to make room for the labels
            except UserWarning:
                return
        elif graph_type == 'Pie Chart':  # Pie Chart
            ax.pie(values, labels=labels, colors=['#facc10', '#a3acff', '#ffb3ff', '#90d595', '#e48381', '#aafbff'], textprops={'color':'white'})
        elif graph_type == 'Bar Graph':
            ax.bar(labels, values, color='#facc10')
            plt.xticks(rotation=15)  # Rotate the x-axis labels and decrease the font size
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", UserWarning)
                    plt.tight_layout()  # Adjust the layout to make room for the labels
            except UserWarning:
                return
        elif graph_type == 'Line Graph':
            ax.plot(labels, values, color='#facc10')
            plt.xticks(rotation=15)  # Rotate the x-axis labels and decrease the font size
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", UserWarning)
                    plt.tight_layout()  # Adjust the layout to make room for the labels
            except UserWarning:
                return
        
        canvas = FigureCanvas(figure)
        scene = QtWidgets.QGraphicsScene()
        scene.addWidget(canvas)
        rect = graphics_view.viewport().rect()
        scene.setSceneRect(QtCore.QRectF(rect))
        graphics_view.setScene(scene)
    
        # Close the figure
        plt.close(figure)
        
class AdminPanel(QtWidgets.QMainWindow):
    def __init__(self, admin_username, db):
        super(AdminPanel, self).__init__()
        self.ui = Ui_AdminPanel()
        self.ui.setupUi(self)
        self.db = db
        self.admin_username = admin_username
        self.load_admin_info()
        self.load_user_list()
        
        # Connect signals
        self.ui.btnUserList_OpenClient.clicked.connect(self.open_client)
        self.ui.btnUserList_MakeAdmin.clicked.connect(self.make_admin)
        self.ui.btnUserList_DeleteUser.clicked.connect(self.delete_user)
        self.ui.btnUserLIst_ChangePassword.clicked.connect(self.change_password)
        self.ui.btnUserList_ChangeUsername.clicked.connect(self.change_username)
        
        # Update Username Input
        self.ui.tableUserList.itemSelectionChanged.connect(self.update_username_input)


    def load_admin_info(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT Fname, Lname FROM users WHERE UserName = %s", (self.admin_username,))
        result = cursor.fetchone()
        if result:
            self.ui.labelHeader_FNameandLnameDynamic.setText(f"{result[0]} {result[1]}")
    
    def update_username_input(self):
        selected_rows = self.ui.tableUserList.selectedItems()
        if selected_rows:
            selected_username = selected_rows[1].text()
            self.ui.inputUserList_Username.setText(selected_username)
            
    def load_user_list(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT ID, UserName, Fname, Lname, UserType FROM users")
        results = cursor.fetchall()
        self.ui.tableUserList.setRowCount(0)
        for row_number, row_data in enumerate(results):
            self.ui.tableUserList.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                if column_number == 4:  # UserType column
                    data = "Admin" if data == 1 else "User"
                self.ui.tableUserList.setItem(row_number, column_number, QTableWidgetItem(str(data)))
    
    def open_client(self):
        username = self.ui.inputUserList_Username.text()
        if username == "":
            QMessageBox.warning(self, 'Open Client', 'Please select a user.')
            return
        self.main = Main(username, self.db)
        self.main.show()
    
    def make_admin(self):
        username = self.ui.inputUserList_Username.text()
        if username == "":
            QMessageBox.warning(self, 'Make Admin', 'Please select a user.')
            return
        if username == self.admin_username:
            QMessageBox.warning(self, 'Make Admin', 'You cannot change your own admin status.')
            return
        cursor = self.db.cursor()
        cursor.execute("SELECT UserType FROM users WHERE UserName = %s", (username,))
        result = cursor.fetchone()
        if result is None:
            QMessageBox.warning(self, 'Make Admin', 'User not found.')
            return
        user_type = result[0]
        if user_type == 1:
            reply = QMessageBox.question(self, 'Make Admin', 'User is already an admin. Are you sure you want to revoke admin privileges?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                cursor.execute("UPDATE users SET UserType = 0 WHERE UserName = %s", (username,))
        elif user_type == 0:
            cursor.execute("UPDATE users SET UserType = 1 WHERE UserName = %s", (username,))
        else:
            QMessageBox.warning(self, 'Make Admin', 'Invalid user type.')
            return
        self.db.commit()
        self.load_user_list()
        
    def change_password(self):
        username = self.ui.inputUserList_Username.text()
        new_password, ok = QInputDialog.getText(self, 'Change Password', 'Enter new password:')
        if ok:
            if new_password.strip() == "":
                QMessageBox.warning(self, 'Change Password', 'Password cannot be blank.')
                return
            cursor = self.db.cursor()
            cursor.execute("UPDATE users SET Password = %s WHERE UserName = %s", (new_password, username))
            self.db.commit()
    
    def change_username(self):
        username = self.ui.inputUserList_Username.text()
        new_username, ok = QInputDialog.getText(self, 'Change Username', 'Enter new username:')
        if ok:
            if new_username.strip() == "":
                QMessageBox.warning(self, 'Change Username', 'Username cannot be blank.')
                return
            cursor = self.db.cursor()
            cursor.execute("SELECT UserName FROM users WHERE UserName = %s", (new_username,))
            if cursor.fetchone() is not None:
                QMessageBox.warning(self, 'Change Username', 'Username already exists.')
                return
            cursor.execute("UPDATE users SET UserName = %s WHERE UserName = %s", (new_username, username,))
            self.db.commit()
            self.load_user_list()

    def delete_user(self):
        username = self.ui.inputUserList_Username.text()
        cursor = self.db.cursor()
        cursor.execute("SELECT ID FROM users WHERE UserName = %s", (username,))
        result = cursor.fetchone()
        if result is None:
            QMessageBox.warning(self, 'Delete User', 'User not found.')
            return
        user_id = result[0]
        reply = QMessageBox.question(self, 'Delete User', 'Are you sure you want to delete this user?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.No:
            return
        cursor.execute("DELETE FROM usersmeters WHERE UserID = %s", (user_id,))
        cursor.execute("DELETE FROM usages WHERE UserID = %s", (user_id,))
        cursor.execute("DELETE FROM usersdevices WHERE UserID = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE UserName = %s", (username,))
        self.db.commit()
        self.load_user_list()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    if not create_connection():
        sys.exit(-1)
    login = Login()
    login.show()
    sys.exit(app.exec())