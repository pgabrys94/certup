from confile import Confile
import paramiko
import os
import json
import subprocess
import time
from datetime import datetime as dt
import jks


name = "CertUp dla DASiUS"
version = 1.0
author = "PG"


#######główna klasa odpowiadająca za przetransportowanie aktualnego skryptu w ustalonym momencie
class CertUpdate:
    def __init__(self):
        pass


############
########klasa obsługi komunikacji email (????????????)
class Sender:
    def __init__(self):
        pass

# funkcja porównująca ustalony w parametrach termin ważności certyfikatu z obecną datą i wysyłająca powiadomienie
# email w przypadku: zbliżającego się terminu wygasania + braku nowego certyfikatu w lokalizacji
# przypisanej do określonego celu


def clean():
    system = os.name

    if system == "nt":
        os.system("cls")
    else:
        os.system("clear")


def connection_ok(ip, port, login, pwd):
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(ip, port, login, pwd)

        transport = ssh.get_transport()

        if transport.is_active():
            ssh.close()
            return True
        else:
            ssh.close()
            return False
    except Exception as err:
        ssh.close()
        print("{}Błąd połaczenia:{} {}".format(red, reset, err))
        return False


def select_certfile():
    global certfile
    choosing = True
    files = os.listdir(certdir)

    for file in files:
        print("[{}] - {}".format(files.index(file) + 1, file))

    print(separator)
    print("[c] - powrót\n")

    while choosing:
        choice = input("Wybierz plik certyfikatów: ")

        if choice == "c":
            print(cancel)
            choosing = False
        elif choice.isdigit():
            if choice in range(1, len(files) + 1):
                certfile = files[int(choice) - 1]
                choosing = False
            else:
                print("Spróbuj ponownie.")
        else:
            print("Spróbuj ponownie.")


def get_config():
    if not os.path.exists(datafilefp):
        data.save()
    else:
        try:
            data.load()
        except Exception as err:
            print(err)
            return False


def target_hosts():
    clean()
    choosing = True

    def new_value(val):
        while True:
            changed_to = input("{}: ".format(val))
            try:
                i = 1
                if val == 0:
                    for num in changed_to.split("."):
                        if int(num) not in range(0, 256):
                            raise Exception("Niewłaściwa wartość {} oktetu.".format(i))
                        i += 1

                    if len(changed_to.split(".")) < 4:
                        raise Exception("Niepoprawny format adresu IP.")
                elif val == 1:
                    if not changed_to.isdigit() or int(changed_to) not in range(0, 65536):
                        raise Exception("Numer portu musi być liczbą z przedziału 0 - 65535")
                else:
                    return changed_to

            except Exception as err:
                print(err)

        def new_pwd():


    def add_host():
        pass

    def edit_host(host_key):
        chooosing = True
        values = data()[host_key]
        options = ["Zmień adres IP", "Zmień port", "Zmień login", "Zmień hasło", "Zmień wykonywane polecenia"]

        while chooosing:
            print(separator)
            print("Edytowany host: {}".format(host_key))
            print(separator)
            print("IP: {}".format(values[0]))
            print("Port: {}".format(values[1]))
            print("Login: {}".format(values[2]))
            print(separator)
            print("Polecenia: {}".format(values[4]))
            print(separator)

            for opt in options:
                print("[{}] - {}".format(options.index(opt), opt))
            print("[c] - powrót\n")
            chooice = input("Wybierz opcję i potwierdź: ")

            if chooice == "c":
                chooosing = False
            elif chooice.isdigit() and int(chooice) in range(1, 6) and int(chooice) != 4:
                value[int(chooice) - 1] = new_value(int(chooice) - 1)
                data.create(host_key=values)
            elif chooice.isdigit() and int(chooice) == 4:
                value[int(chooice) - 1] = new_pwd()
                data.create(host_key=values)

    while choosing:
        print(separator)
        print("Hosty docelowe:")
        print(separator)

        if len(data()) != 0:
            for key, value in data().items():
                print("[{}] - {} [{}:{}] - {}".format(key.index(), key, value[0], value[1], value[2]))
        else:
            print("Brak zdefiniowanych hostów.")
            print(separator)

        print("[c] - powrót")
        print("[d] - dodaj nowego hosta")
        if len(data()) != 0:
            print("[{}-{}] - wybierz hosta do edycji".format(1, len(data())))
        choice = input("Wybierz opcję i potwierdź: ")

        if choice == "c":
            print(cancel)
            choosing = False
        elif choice == "d":
            add_host()
        elif choice.isdigit() and int(choice) in range(1, len(data()) + 1):
            edit_host(list(data())[int(choice)])
        else:
            print("Spróbuj ponownie.")


# MISC
green = "\033[92m"
red = "\033[91m"
blue = "\033[94m"
yellow = "\033[93m"
reset = "\033[0m"
welcome = "{} v{} by {}".format(name, version, author)
separator = "-" * len(welcome)
cancel = "\n{}POWRÓT...{}".format(blue, reset)
try_again = "{0}\n{1:^{width}}\n{0}".format(separator, "SPRÓBUJ PONOWNIE", width=len(separator))


# MAIN
running = True
certdir = os.path.join(os.getcwd(), "configs")
certfile = ""
certfilefp = os.path.join(certdir, certfile)
datadir = os.path.join(os.getcwd(), "certs")
datafile = certfile + ".json"
datafilefp = os.path.join(datadir, datafile)
data = Confile(datafile, datadir)

menu = ["Wskaż plik certyfikatu", "Zakończ"]

menu_full = {
    "Wyświetl certyfikaty i ich daty ważności": ls_certs,
    "Zaktualizuj certyfikaty": up_certs,
    "Wskaż plik certyfikatu": select_certfile,
    "Hosty docelowe": target_hosts,
    "Zakończ": None
}

while running:
    clean()
    print("{0}\n{1}\n{0}\n".format(separator, welcome))

# sprawdź czy plik jest wybrany, jeśli tak to print OPERUJESZ NA... + usuwanie opcji wyświetl i zaktualizuj
    if certfile != "":
        print("\n{}OPERUJESZ NA PLIKU: {}{}\n".format(green, certfile, reset))
        get_config()
        menu.insert(0, menu_full[0])
        menu.insert(1, menu_full[1])
        menu.insert(3, menu_full[3])
    else:
        print("\n{}WYBIERZ PLIK CERTYFIKATU{}\n".format(red, reset))

# sprawdź czy zdefiniowane są hosty docelowe w pliku konfiguracyjnym, jeśli tak to STATUS POŁĄCZENIA...
    if len(data()) != 0:
        print("STATUS POŁĄCZENIA:\n")
        for k, v in data().items():
            print("{}{}[{}]{}".format(green if connection_ok(v[0], v[1], v[2], v[3]) else red, k, v[0], reset))

    for pos in menu:
        print("[{}] - {}".format(menu.index(pos) + 1, pos))


