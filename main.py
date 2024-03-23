from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
import yfinance as yf
import numpy
import json
from datetime import datetime
from plyer import notification


def HisseGecmisiniCek(hisseadi, interval):
    data= yf.Ticker(hisseadi)
    if(interval=="5m"):
        aralik="60d"
    return(data.history(period=aralik, interval=interval))

def TrailingStopSmaSinyal(atr_carpan, atr_day, sma_day, hisse_gecmisi, aralik, hisse_adi):
    hissegecmisi = hisse_gecmisi
    pozisyon = 0
    pozisyona_girilen_mum = 0
    stoplosstavani = 0
    start = 0
    if(atr_day<sma_day):
        start = sma_day
    else:
        start = atr_day
    for i in range(start, len(hisse_gecmisi)-1):
        atr=0
        for j in range(i-atr_day,i):
            if (hissegecmisi[j][1]>hissegecmisi[j][3]):
                atr+=100-(hissegecmisi[j][3]*100/hissegecmisi[j][1])
            else:
                atr+=(hissegecmisi[j][3]*100/hissegecmisi[j][1])-100
        atr=atr/atr_day
        atr*=atr_carpan/10

        sma = 0
        for j in range(i-sma_day,i):
            sma += hissegecmisi[j][3]
        sma = sma/sma_day

        if(i==start):
            pozisyon = 1
            stoplosstavani=hissegecmisi[i][3]
        elif((hissegecmisi[i][3]<stoplosstavani*(100-atr)/100)and(pozisyon==1)):
            pozisyon=2
            pozisyona_girilen_mum = i
            stoplosstavani=hissegecmisi[i][3]
        elif((hissegecmisi[i][3]>stoplosstavani*(100-atr)/100)and(pozisyon==1)):
            if(hissegecmisi[i][3]>stoplosstavani):
                stoplosstavani=hissegecmisi[i][3]
        elif((hissegecmisi[i][3]<stoplosstavani*(100+atr)/100)and(pozisyon==2)):
            if(hissegecmisi[i][3]<stoplosstavani):
                stoplosstavani=hissegecmisi[i][3]
        elif((hissegecmisi[i][3]>stoplosstavani*(100+atr)/100)and(pozisyon==2)and(hissegecmisi[i][3]>sma)):
            pozisyon=1
            pozisyona_girilen_mum = i
            stoplosstavani=hissegecmisi[i][3]
    if(pozisyon==1):
        pozisyon = 'AL'
    else:
        pozisyon = 'SAT'
    return [len(hissegecmisi)-pozisyona_girilen_mum-1, pozisyon]

def unique_2d_array(arr):
    unique_elements = set()
    result = []
    for sublist in arr:
        unique_sublist = tuple(sublist)
        if unique_sublist not in unique_elements:
            unique_elements.add(unique_sublist)
            result.append(sublist)
    return result

def save_settings(settings):
    with open('settings.json', 'w') as file:
        json.dump(settings, file)

def send_notification(hisse, pozisyon_yonu):
    title = hisse+' '+pozisyon_yonu
    message = hisse+' '+pozisyon_yonu+' @ '+datetime.now().strftime('%H:%M:%S')
    notification.notify(title=title, message=message)

def load_settings():
    try:
        with open('settings.json', 'r') as file:
            data = json.load(file)

        # Okunan verileri değişkenlere atama
        checkboxed_index = data.get("checkboxed_index", [])
        max_pozisyon_sayisi = data.get("max_pozisyon_sayisi", [0])
        return checkboxed_index, max_pozisyon_sayisi
    except FileNotFoundError:
        # Dosya bulunamazsa veya okunamazsa varsayılan ayarları döndür
        return [],[0]


checkboxed_index, max_pozisyon_sayisi = load_settings()

class SettingsScreen(Screen):
    def __init__(self, main_screen, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.main_screen = main_screen
        strateji_array = self.main_screen.strateji_array
        layout = GridLayout(cols=2)
        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        scrollview.add_widget(layout)
        self.add_widget(scrollview)
        self.checkboxed_index=[]

        layout.add_widget(Label(text='Max Pozisyon'))
        self.max_pozisyon = TextInput(multiline=False, text=str(max_pozisyon_sayisi[0]))
        layout.add_widget(self.max_pozisyon)


        layout.add_widget(Button(text='Geri Dön', on_press=self.go_back))

    def go_back(self, instance):
        # Ayarlar ekranından ana ekrana dönmek için kullanılacak metod
        self.manager.current = 'main'
        max_pozisyon_sayisi[0] = int(self.max_pozisyon.text)
    


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.strateji_array = [
            ['GARAN', '5m', 'TS&SMA', [69,32,90], ''],
            ['GARAN', '5m', 'TS&SMA', [40,2,200], ''],
            ['THYAO', '5m', 'TS&SMA', [40,2,200], ''],
            ['GARAN', '5m', 'TS&SMA', [60,1,178], '']
        ]
        self.label_dict = {}
        self.data_history = {}
        self.data_history_list = []
        main_layout = BoxLayout(orientation='vertical')

        scrollview = ScrollView(size_hint=(1, None), size=(Window.width, Window.height*9/10))
        layout = GridLayout(cols=4, size_hint_y=None)  # Tabloda 3 sütun
        layout.height = Window.height/10*6

        layout.add_widget(Label(text='Son Güncelleme Zamanı'))
        self.guncel_label = Label(text='')
        layout.add_widget(self.guncel_label)
        layout.add_widget(Label(text='Saat'))
        self.saat_label = Label(text='')
        layout.add_widget(self.saat_label)

        layout.add_widget(Label(text='Hisse Adı'))
        layout.add_widget(Label(text='Strateji'))
        layout.add_widget(Label(text='Durum'))
        layout.add_widget(Label(text='Pozisyonda mı?'))

        for i in range(len(self.strateji_array)):
            self.data_history_list.append([self.strateji_array[i][0],self.strateji_array[i][1]])
            self.label_dict[str(i)] = [
            Label(text=f'{self.strateji_array[i][0]} ({self.strateji_array[i][1]})', color=(1, 1, 1, 1)),
            Label(text=f'{self.strateji_array[i][2]}\nAtr Çarpan={self.strateji_array[i][3][0]} Atr Periyot={self.strateji_array[i][3][1]} Sma Periyot={self.strateji_array[i][3][2]}', color=(1, 1, 1, 1)),
            Label(text=f'{self.strateji_array[i][4]}', color=(1, 1, 1, 1))
            ]
        self.data_history_list = unique_2d_array(self.data_history_list)
        # Veri satırları
        self.indis = 0
        for i in self.label_dict.values():  # Örnek olarak 5 satır ekliyoruz
            layout.add_widget(i[0])
            layout.add_widget(i[1])
            layout.add_widget(i[2])
            checkbox = CheckBox(active=True if self.indis in checkboxed_index else False)
            layout.add_widget(checkbox)
            checkbox.bind(active=lambda instance, value, index=self.indis: self.checkbox_func(value, index))
            self.indis += 1

        scrollview.add_widget(layout)

        bottom_layout = GridLayout(cols=2, size_hint_y=Window.height/10)
        settings_button = Button(text='Ayarlar', size_hint_y=1, size_hint_x=1)
        settings_button.bind(on_press=self.show_settings)
        bottom_layout.add_widget(settings_button)

        self.button_stop = Button(text='Alarmı Durdur', size_hint=(1, 1), disabled=True)
        self.button_stop.bind(on_press=self.stop_alarm)
        bottom_layout.add_widget(self.button_stop)
        main_layout.add_widget(scrollview)
        main_layout.add_widget(bottom_layout)
        self.add_widget(main_layout)

        Clock.schedule_once(self.PozisyonCheck, 0)

        Clock.schedule_interval(self.update_time, 1)

    def show_settings(self, instance):
        # Ayarlar ekranını açmak için kullanılacak metod
        self.manager.current = 'settings'

    def update_time(self, dt):
        tam_saat = datetime.now().strftime('%H:%M:%S')
        self.saat_label.text = tam_saat
        saat = datetime.now().hour
        dakika = datetime.now().minute
        saniye = datetime.now().second
        if (9 <= saat <= 18)and(dakika%5==0)and(saniye==10):
            Clock.schedule_once(self.PozisyonCheck, 0)
            self.guncel_label.text = tam_saat
        elif (dakika%5==0)and(saniye==10):
            self.guncel_label.text = 'Piyasa Kapalı'

    def checkbox_func(self, value, indis):
        if value:
            checkboxed_index.append(indis)
        else:
            checkboxed_index.remove(indis)
        checkboxed_index.sort(reverse=True)

    def start_alarm(self, instance):
        self.alarm_sound = SoundLoader.load('smoke.mp3')
        if self.alarm_sound:
            self.alarm_sound.play()
            self.button_stop.disabled = False   

    def stop_alarm(self, instance):
        if self.alarm_sound:
            self.alarm_sound.stop()
            self.button_stop.disabled = True

    def PozisyonCheck(self, dt):  # dt parametresi, Clock tarafından otomatik olarak iletilir

        for i in self.data_history_list:
            gecmis = HisseGecmisiniCek(str(i[0])+'.is',i[1])
            self.data_history[i[0]+i[1]] = gecmis.to_numpy()

        for indis, i in enumerate(self.strateji_array):
            if(i[2]=='TS&SMA'):
                sonuc_array = TrailingStopSmaSinyal(i[3][0], i[3][1], i[3][2], self.data_history[i[0]+i[1]], i[1], i[0]+".is")
            if not (sonuc_array[-1] in self.label_dict[str(indis)][2].text):
                if(sonuc_array[-1]=='AL')and(int(max_pozisyon_sayisi[0])>len(checkboxed_index)and('SAT' in self.label_dict[str(indis)][2].text)):
                    send_notification(i[0],sonuc_array[-1])
                    start_alarm()
                elif(sonuc_array[-1]=='SAT')and(indis in checkboxed_index)and('AL' in self.label_dict[str(indis)][2].text):
                    send_notification(i[0],sonuc_array[-1])
                    start_alarm()
                if (sonuc_array[-1]=="AL"):
                    self.label_dict[str(indis)][0].color = (0, 1, 0, 1)
                    self.label_dict[str(indis)][1].color = (0, 1, 0, 1)
                    self.label_dict[str(indis)][2].color = (0, 1, 0, 1)
                else:
                    self.label_dict[str(indis)][0].color = (1, 0, 0, 1)
                    self.label_dict[str(indis)][1].color = (1, 0, 0, 1)
                    self.label_dict[str(indis)][2].color = (1, 0, 0, 1)
            self.label_dict[str(indis)][2].text = sonuc_array[-1]+"\n"+str(sonuc_array[0])+" Mum Önce"
    


class TableApp(App):
    def build(self):
        # ScreenManager oluştur
        screen_manager = ScreenManager()

        # Ana ekranı oluştur ve ScreenManager'a ekle
        main_screen = MainScreen(name='main')
        screen_manager.add_widget(main_screen)

        # Ayarlar ekranını oluştur ve ScreenManager'a ekle
        settings_screen = SettingsScreen(main_screen,name='settings')
        screen_manager.add_widget(settings_screen)
        return screen_manager

    def on_stop(self, *args):
        data = {
            "checkboxed_index": checkboxed_index,
            "max_pozisyon_sayisi": max_pozisyon_sayisi
        }
        with open('settings.json', 'w') as file:
            json.dump(data, file)
        


if __name__ == '__main__':
    Window.clearcolor = ((135 / 255), (135 / 255), (135 / 255), 1)
    # DataService().start()
    TableApp().run()
