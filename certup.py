from conson import Conson
import paramiko
import os
import subprocess
import shutil


name = "CertUp dla DASiUS"
version = 1.0
author = "PG"

# ZMIENNE:
running = True
certdir = os.path.join(os.getcwd(), "certs")
certfile = ""
certfilefp = None
datadir = os.path.join(os.getcwd(), "configs")
datafile = None
datafilefp = ""
data = Conson()
setup = False
error = ""
keystore_pwd = ""
uni_val = ["IP", "Port", "Login", "Hasło", "Komendy"]

#######główna klasa odpowiadająca za przetransportowanie aktualnego skryptu w ustalonym momencie
class CertUpdate:
    def __init__(self):
        pass


def clean(ex=False):
    system = os.name

    if system == "nt":
        os.system("cls")
    else:
        os.system("clear")
    if not ex:
        print("{0}\n{1}\n{0}\n".format(separator, welcome))
    return ""


def clean_decor(func):
    def f(*args, **kwargs):
        clean()
        return func(*args, **kwargs)
    return f


@clean_decor
def share_cert():
    global certfile
    global certdir
    global certfilefp
    global datafile
    global datafilefp
    global datadir
    global setup
    global keystore_pwd

    certfile = input("Wprowadź przyjazną nazwę dla pliku certyfikatu: ")
    keystore_pwd = input("Wprowadź hasło do magazynu kluczy: ")
    cacfp = os.path.join(r"/etc/ssl/certs/java", "cacerts")

    certfilefp = os.path.join(certdir, certfile)
    datafile = certfile + ".json"
    datafilefp = os.path.join(datadir, datafile)
    data.file = datafilefp
    setup = True
    try:
        if not os.path.exists(cacfp):
            cacfp = r"{}".format(input("Wprowadź ścieżkę absolutną pliku 'cacerts': "))

        shutil.copy(cacfp, certfilefp)

        data.save()
    except Exception as err:
        print(err)


@clean_decor
def ls_certs():
    global keystore_pwd
    global certfilefp
    choosing = True
    lsmenu = ["Wyświetl wszystkie nazwy", "Wyświetl datę utworzenia certyfikatu", "Wyświetl certyfikat"]

    try:

        output = subprocess.check_output(["keytool", "-list", "-keystore", f"{certfilefp}",
                                          "-storepass", f"{keystore_pwd}", "-rfc"], text=True)

        while choosing:
            for lspos in lsmenu:
                print("[{}] - {}".format(lsmenu.index(lspos) + 1, lspos))
            print("[c] - powrót\n")
            choice = input("Wybierz opcję i potwierdź: ")

            if choice == "c":
                choosing = False
            elif choice.isdigit() and int(choice) in range(1, 4):
                choice = int(choice) - 1
                if choice == 0:
                    print("opt1")
                    result = ""
                    for line in output.split("\n"):
                        if "alias name" in line.lower():
                            result += line[line.index(":") + 1:]
                    print("wynik: ",result)
                    pause = input("pause...")
                elif choice == 1:
                    print("opt2")
                elif choice == 2:
                    print("opt3")
            else:
                print(try_again)

    except Exception as err:
        print(err)
################################
        # specific_certs = input("Wprowadź nazwy kluczowych certyfikatów (separator: ; ): ").replace(" ", "").split(";")

        # cert_dict = {}
        # all_alias = []
        #
        # keytool_list = subprocess.run(["keytool", "-list", "-keystore", f"{certfilefp}", "-storepass",
        #                 f"{keystore_pwd}", "-rfc", "-file", f"{certfilefp}"])


        # for line in keytool_list:
        #     if "alias name" in line.lower():
        #         all_alias.append((line.split(":", 1)[1].strip()))
        #
        # if len(specific_certs) != 0:
        #     multialias = ""
        #     for certname in specific_certs:
        #         multialias += certname
        #         if certname in all_alias:
        #             output = subprocess.check_output(["keytool", "-list", "-cacerts", "-storepass", f"{keystore_pwd}", "-rfc", "-alias", f"{certname}"], text=True).split("\n\n")[1].replace("\n", "")
        #             cert_dict[certname] = [output[:27], output[27:-25], output[-25:]]
        # else:
        #     for alias in all_alias:
        #         output = subprocess.check_output(["keytool", "-list", "-cacerts", "-storepass", f"{keystore_pwd}", "-rfc", "-alias", f"{alias}"], text=True).split("\n\n")[1].replace("\n", "")
        #         cert_dict[alias] = [output[:27], output[27:-25], output[-25:]]
        # print(cert_dict)
        # cert1 = cert_dict[list(cert_dict)[0]]
        # print(cert1)
        # input("wait")


def check_structure():
    need_restart = False
    if not os.path.exists(datadir):
        os.mkdir(datadir)
        need_restart = True
    if not os.path.exists(certdir):
        os.mkdir(certdir)
        need_restart = True
    if need_restart:
        print("Utworzono strukturę katalogów. Umieść plik certyfikatów w folderze 'certs' i uruchom ponownie program.")
        return True


def jdk_present():
    try:
        result = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True).split("\n")
        for line in result:
            if "openjdk version" in line:
                return True
    except Exception:
        return False


def connection_ok(ip, port, login, pwd):
    global error
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
        error = str(err).split("]")[1]
        ssh.close()
        return False


@clean_decor
def select_certfile():
    global certfile
    global certdir
    global certfilefp
    global datafile
    global datafilefp
    global setup
    global keystore_pwd
    choosing = True
    files = os.listdir(certdir)
    i = 0
    for file in files:
        print("[{}] - {}".format(files.index(file) + 1, file))
        i += 1

    print(separator)
    print("[c] - powrót\n")

    while choosing:
        choice = input("Wybierz plik certyfikatów: ")
        if choice == "c":
            print(cancel)
            certfile = certfile
            choosing = False
        elif choice.isdigit():
            if int(choice) in range(1, len(files) + 1):
                certfile = files[int(choice) - 1]
                certfilefp = os.path.join(certdir, certfile)
                datafile = certfile + ".json"
                datafilefp = os.path.join(datadir, datafile)
                data.file = datafilefp
                setup = True
                choosing = False
                keystore_pwd = input("Wprowadź hasło do magazynu kluczy: ")
            else:
                print(try_again)
        else:
            print(try_again)


def get_config():
    if not os.path.exists(datafilefp):
        data.save()
    else:
        try:
            data.load()
        except Exception as err:
            print(err)
            return False


def salt_edit():
    new_salt = input("Wprowadź klucz: ")
    if new_salt == "":
        print(cancel)
    else:
        data.salt = new_salt
        return "{}KLUCZ ZOSTAŁ ZMIENIONY{}".format(green, reset)


def up_certs():
    pass


@clean_decor
def target_hosts():
    choosing = True

    @clean_decor
    def new_value(val):
        while True:
            changed_to = input("{}".format(val))
            try:
                i = 1
                if "IP" in val:
                    for num in changed_to.split("."):
                        if int(num) not in range(0, 256):
                            raise Exception("Niewłaściwa wartość {} oktetu.".format(i))
                        i += 1

                    if len(changed_to.split(".")) < 4:
                        raise Exception("Niepoprawny format adresu IP.")
                    else:
                        return changed_to
                elif "Port" in val:
                    if not changed_to.isdigit() or int(changed_to) not in range(1, 65536):
                        raise Exception("Numer portu musi być liczbą z przedziału 1 - 65535")
                    else:
                        return changed_to
                else:
                    return changed_to

            except Exception as err:
                print(err)

    @clean_decor
    def add_host():
        vrs = {
            "Nazwa hosta: ": None,
            f"{uni_val[0]}: ": None,
            f"{uni_val[1]}: ": None,
            f"{uni_val[2]}: ": None,
            f"{uni_val[3]}: ": None,
            f"{uni_val[4]} do wykonania na hoście\n(każdą komendę oddziel znakiem #): ": []
        }
        vrsl = list(vrs)

        for var in vrsl:
            vrs[var] = new_value(var)
        values = {"h^" + vrs[vrsl[0]]: [vrs[vrsl[1]], vrs[vrsl[2]], vrs[vrsl[3]], vrs[vrsl[4]], vrs[vrsl[5]]]}
        data.create(**values)
        data.veil(vrs[vrsl[0]], 3)
        data.save()

    @clean_decor
    def edit_host(host_key):
        chooosing = True
        changed = False
        values = data()[host_key]

        while chooosing:
            print(separator)
            print("Edytowany host: {}".format(host_key))
            print(separator)
            print("IP: {}".format(values[0]))
            print("Port: {}".format(values[1]))
            print("Login: {}".format(values[2]))
            print(separator)
            print("Komendy: {}".format(values[4]))
            print(separator)

            for opt in uni_val:
                print("[{}] - {}{}".format(uni_val.index(opt) + 1, "Zmień ", opt if opt == uni_val[0] else opt.lower()))
            print("[c] - powrót\n")
            chooice = input("Wybierz opcję i potwierdź: ")

            if chooice == "c":
                if changed:
                    data.save()
                chooosing = False
            elif chooice.isdigit() and int(chooice) in range(1, 6):
                changed = True
                value[int(chooice) - 1] = new_value(uni_val[int(chooice) - 1])
                data.create(host_key=[values])
                data.veil(data()[host_key][3])

    @clean_decor
    def delete_host(host_key):
        print(key)
        data.dispose(host_key)
        data.save()

    while choosing:
        print(separator)
        print("Hosty docelowe:")
        print(separator)

        if len(data()) != 0:
            for key, value in data().items():
                print("[{}] - {} [{}:{}] - {}".format(list(data()).index(key) + 1, key, value[0], value[1], value[2]))
            print(separator)
        else:
            print("Brak zdefiniowanych hostów.")
            print(separator)

        if len(data()) != 0:
            print("[{}-{}] - wybierz hosta do edycji".format(1, len(data())))
            print("[d] + [{}-{}] - usuń hosta".format(1, len(data())))
        print("[a] - dodaj nowego hosta")
        print("[c] - powrót\n")
        choice = input("Wybierz opcję i potwierdź: ")
        if choice == "c":
            print(cancel)
            choosing = False
        elif choice == "a":
            add_host()
        elif "d" in choice:
            try:
                number = ""
                for x in choice:
                    if x.isdigit():
                        number += x
                delete_host(list(data())[int(number) - 1])
            except Exception:
                print(try_again)
        elif choice.isdigit() and int(choice) in range(1, len(data()) + 1):
            edit_host(list(data())[int(choice) - 1])
        else:
            print(try_again)


# MISC
green = "\033[92m"
red = "\033[91m"
blue = "\033[94m"
yellow = "\033[93m"
reset = "\033[0m"
welcome = "{} v{} by {}".format(name, version, author)
separator = "-" * len(welcome)
cancel = "\n{}POWRÓT...{}".format(blue,  reset)
try_again = "\n{}{}SPRÓBUJ PONOWNIE...{}".format(clean(), red, reset)


# MAIN
if check_structure():
    exit()

menu = ["Wybierz plik magazynu kluczy", "Zakończ"]

menu_full = {
    "Wyświetl certyfikaty i daty utworzenia": ls_certs,
    "Zaktualizuj certyfikaty": up_certs,
    "Wybierz plik magazynu kluczy": select_certfile,
    "Wykorzystaj lokalny magazyn kluczy": share_cert,
    "Hosty docelowe": target_hosts,
    "Zmień klucz": salt_edit,
    "Zakończ": None
}

while running:
    clean()
# sprawdź czy plik jest wybrany, jeśli tak to print OPERUJESZ NA... + usuwanie opcji wyświetl i zaktualizuj
    if certfile != "":
        print("{}OPERUJESZ NA PLIKU: {}{}".format(green, certfile, reset))
        get_config()
        if setup:
            menu.pop(menu.index(list(menu_full)[3]))
            menu.insert(0, list(menu_full)[0])
            menu.insert(1, list(menu_full)[1])
            menu.insert(3, list(menu_full)[4])
            menu.insert(4, list(menu_full)[5])
        setup = False
    else:
        print("\n{}WYBIERZ PLIK CERTYFIKATU{}\n".format(red, reset))
        if jdk_present():
            if list(menu_full)[3] not in menu:
                menu.insert(1, list(menu_full)[3])


# sprawdź czy zdefiniowane są hosty docelowe w pliku konfiguracyjnym, jeśli tak to STATUS POŁĄCZENIA...
    if len(data()) != 0:
        print("\nSTATUS POŁĄCZENIA:\n")
        for k, v in data().items():
            print("{}{} {} {}{}".format(green if connection_ok(v[0], v[1], v[2], v[3]) else red,
                                        k, "-" if error != "" else "", error.strip(), reset))

    print("\n{}".format(separator))
    for pos in menu:
        print("[{}] - {}".format(menu.index(pos) + 1, pos))

    u_in = input("\nWybierz opcję, [Enter] zatwierdza: ")
    try:
        if int(u_in) <= 0:
            raise Exception("input less or equal to 0")
        elif list(menu_full)[6] == menu[int(u_in) - 1] and u_in != "0":
            clean(True)
            exit()
        else:
            menu_full[menu[int(u_in) - 1]]()
    except Exception:
        print(try_again)
