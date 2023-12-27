import os
import subprocess
import shutil
import time
import paramiko
from conson import Conson
import jks
import base64
import textwrap
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


# Informacje
name = "CertUp"
version = 1.15
author = "PG/DASiUS"    # https://github.com/pgabrys94

# Zmienne globalne:
ksdir = os.path.join(os.getcwd(), "keystores")
ksfile = ""
ksfilefp = ""
certdir = os.path.join(os.getcwd(), "certs")
datadir = os.path.join(os.getcwd(), "configs")
datafile = None
datafilefp = ""
setup = False
error = ""  # pozwala na wyświetlenie błędu przy nieosiągalnym hoście docelowym.
keystore_pwd = ""
uni_val = ["IP", "Port", "Login", "Hasło", "Komendy"]
conn_status = {}
host_status_fresh = False

# Utworzenie instancji klasy parametrów.
data = Conson()


class Remote:
    """
    Klasa tworząca obiekty do manipulacji zdalnym hostem. Atrybutami instancji takiej klasy są dane zawarte
    w słowniku parametrów instancji conson.
    """
    def __init__(self, hostname, ip, port, login, pwd, command_list, verbose=False):
        self.hostname = hostname
        self.ip = ip
        self.port = port
        self.login = login
        self.pwd = pwd
        self.commands = command_list
        self.terminal = paramiko.SSHClient()
        self.path = os.path.join("/", "home", self.login, "certup") if self.login != "root"\
            else os.path.join("/", "root", "certup")
        self.backup_path = os.path.join(self.path, "backup")
        self.verbose = verbose

    def connect(self):
        """
        Funkcja otwierająca połączenie SSH pomiędzy hostem źródłowym a docelowym.
        :return:
        """
        try:
            self.terminal.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            self.terminal.connect(self.ip, port=self.port, username=self.login, password=self.pwd)
            if self.verbose:
                print("\n{}POŁĄCZONO z {}{}".format(green, self.hostname, reset))
        except Exception as err:
            if self.verbose:
                print("{}BŁĄD POŁĄCZENIA z {}{}: {}".format(red, self.hostname, reset, err))

    def disconnect(self):
        """
        Zamykanie połączenia między hostami.
        :return:
        """
        self.terminal.close()
        if self.verbose:
            print("{}ROZŁĄCZONO z {}{}".format(green, self.hostname, reset))

    def create_tree(self):
        """
        Funkcja tworząca strukturę katalogów na hoście docelowym.
        :return:
        """
        with self.terminal.open_sftp() as sftp:
            try:
                sftp.stat(self.path)
                print("{}Struktura katalogów już istnieje.{}".format(blue, reset))
            except Exception:
                print("Tworzenie struktury katalogów...")
                try:
                    sftp.mkdir(self.path)
                except Exception as err:
                    print("{}Błąd tworzenia struktury katalogów: {}".format(red, reset), err)

    def import_jks(self, srcpwd, destpwd):
        """
        Funkcja wykonująca komendę importowania przesłanego magazynu kluczy do lokalnego magazynu na hoście docelowym.
        :param srcpwd: Hasło do otwarcia magazynu kluczy, domyślnie "changeit".
        :param destpwd: Hasło do otwarcia magazynu kluczy, domyślnie "changeit".
        :return:
        """
        command = (f"keytool -importkeystore -deststorepass {destpwd} -cacerts -srckeystore"
                   f" {os.path.join(self.path, 'cacerts')} -srcstorepass {srcpwd} -noprompt")
        if self.verbose:
            print("Importowanie magazynu kluczy...")
        try:
            self.terminal.exec_command(command)
            if self.verbose:
                print("{}Zaimportowano magazyn kluczy.{}".format(green, reset))
        except Exception as err:
            if self.verbose:
                print("{}Błąd importowania magazynu kluczy: {}".format(red, reset), err)

    def run(self):
        """
        Funkcja wykonywania komend na hoście zdalnym.
        :return:
        """
        if self.commands:
            for command in self.commands:
                try:
                    if self.verbose:
                        print("Wykonywanie komendy: {}".format(command))
                    self.terminal.exec_command(command)
                    time.sleep(1)
                except Exception as err:
                    if self.verbose:
                        print("{}Błąd komendy: {}{}: {}".format(red, reset, command, err))

    def upload(self, file):
        """
        Funkcja odpowiedzialna za przesyłanie magazynu kluczy do hosta zdalnego.
        :param file: Pełna ścieżka do pliku magazynu kluczy.
        :return:
        """
        try:
            if self.verbose:
                print("Wysyłanie...")
            sftp = self.terminal.open_sftp()
            sftp.put(file, os.path.join(self.path, "cacerts"))
            sftp.close()
            if self.verbose:
                print("{}Wysłano: {}:{}{}".format(green, self.ip, os.path.join(self.path, "cacerts"), reset))
        except Exception as err:
            if self.verbose:
                print("{}Błąd wysyłania{}: {}".format(red, reset, err))


def clean(ex=False):
    """
    Funkcja czyszcząca okno konsoli podczas poruszania się po interfejsie CLI i wstawiająca nagłówek z nazwą programu.
    :param ex: Bool -> czy funkcja zostaje wywołana podczas zakończenia programu. PRAWDA: nagłówek nie zostanie dodany.
    :return:
    """
    system = os.name

    if system == "nt":
        os.system("cls")
    else:
        os.system("clear")
    if not ex:
        print("{0}\n{1}\n{0}\n".format(separator, welcome))
    return ""


def clean_decor(func):
    """
    Dekorator funkcji.
    :param func: Funkcja
    :return:
    """
    def f(*args, **kwargs):
        clean()
        return func(*args, **kwargs)
    return f


@clean_decor
def up_ks():
    def execute(target):
        target.connect()
        target.create_tree()
        target.upload(ksfilefp)
        target.import_jks(keystore_pwd, keystore_pwd)
        target.run()
        target.disconnect()
        return

    def up_single(host):  # Wgraj na pojedyńczego hosta
        target = Remote(host, data()[host][0], data()[host][1], data()[host][2],
                        data.unveil(data()[host][3]), data()[host][4], True)

        execute(target)
        input("\n[enter] - kontynuuuj...")
        return

    @clean_decor
    def up_all():  # Wgraj na wszystkie hosty
        try:
            for key, value in data().items():
                if conn_status[key]:
                    target = Remote(key, value[0], value[1], value[2], data.unveil(value[3]), value[4], True)

                    execute(target)

            input("\n[enter] - kontynuuuj...")
            return
        except Exception:
            clean()
            return

    @clean_decor
    def choose_target():
        choosing_host = True
        while choosing_host:
            print(separator)
            print("Hosty docelowe:")
            print(separator)

            printed_hosts = 0
            if len(data()) != 0:
                for key, value in data().items():
                    if conn_status[key]:
                        printed_hosts += 1
                        print("[{}] - {} [{}:{}] - {}"
                              .format(printed_hosts, key, value[0], value[1], value[2]))
                print(separator)
            else:
                print("Brak zdefiniowanych hostów.")
                print(separator)

            if printed_hosts > 0:
                print("[{}-{}] - wybierz hosta".format(1, printed_hosts))
            print("\n[c] - powrót\n")
            choice = input("Wybierz opcję i potwierdź: ")

            if choice == "c":
                clean()
                choosing_host = False
            elif choice.isdigit() and int(choice) in range(1, len(data()) + 1):
                up_single(list(data())[int(choice) - 1])
            else:
                clean()
                print(try_again)

    options = {"Wgraj na pojedyńczego hosta": choose_target, "Wgraj na wszystkie zdefiniowane hosty": up_all}
    choosing = True
    while choosing:
        for opt in options:
            print("[{}] - {}".format(list(options).index(opt) + 1, opt))
        print("\n[c] - powrót")

        uin = input("\nWybierz opcję, [Enter] zatwierdza: ")
        try:
            if uin.lower() == "c":
                clean()
                choosing = False
                return
            elif uin.isdigit() and int(uin) <= 0:
                raise Exception("input less or equal to 0")
            else:
                options[list(options)[int(uin) - 1]]()
        except Exception:
            clean()
            print(try_again)


@clean_decor
def share_ks():
    """
    Funkcja eksportu magazynu kluczy z hosta źródłowego.
    :return:
    """

    def locate_java_ks():
        """
        Funkcja ustalająca ścieżkę magazynu kluczy Java.
        :return: String or False -> Zwraca kompletną ścieżkę lub FAŁSZ
        """
        try:
            raw_request = subprocess.Popen(
                ["java", "-XshowSettings:properties", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            o, e = raw_request.communicate()

            default_dir_structure = r"lib/security/cacerts"
            for line in e.split("\n"):
                print(line)
                if "java.home" in line:
                    request = line.split("=")[1].strip()
                    java_cert_path = os.path.join(request, default_dir_structure)
                    return java_cert_path
            return False
        except Exception as er:
            print(er)
            return False

    global ksfile
    global ksdir
    global ksfilefp
    global datafile
    global datafilefp
    global datadir
    global setup
    global keystore_pwd

    if ksfile == "":
        setup = True

    while True:
        ksfile = input("Wprowadź przyjazną nazwę dla pliku magazynu kluczy: ")
        if ksfile != "":
            break
        print("{}Błąd:{} Nazwa nie może być pusta.".format(red, reset))
    keystore_pwd = input("Wprowadź hasło do magazynu kluczy (domyślnie: changeit): ")
    keystore_pwd = "changeit" if keystore_pwd == "" else keystore_pwd

    ksfilefp = os.path.join(ksdir, ksfile)
    datafile = ksfile + ".json"
    datafilefp = os.path.join(datadir, datafile)
    data.file = datafilefp
    try:
        cacfp = locate_java_ks()
        if cacfp is False:
            print("is false")
            cacfp = r"{}".format(input("Wprowadź ścieżkę absolutną do magazynu kluczy (cacerts): "))

        if not os.path.exists(cacfp):
            raise Exception("Podany magazyn kluczy nie istnieje.")
        else:
            shutil.copy(cacfp, ksfilefp)

        data.save()
    except Exception as err:
        print(err)


@clean_decor
def ls_ks():
    """
    Funkcja menu wyświetlania zawartości magazynu kluczy.
    :return:
    """
    global keystore_pwd
    global ksfilefp

    def print_aliases(keystore):
        """
        Wyświetl wszystkie aliasy w magazynie kluczy.
        :param keystore: Zawartość magazynu kluczy.
        :return:
        """
        result = ""
        column = 2
        width = 80
        for i, alias in enumerate(list(keystore.certs), start=1):
            result += alias
            formatted = "{:<{}}".format(alias, width)
            print(formatted, end="\n" if i % column == 0 else " ")
        print("")
        print("{0}\n{1}\n{0}\n".format(separator, welcome))

    def print_certificate(keystore):
        """
        Wyświetl klucz certyfikatu i datę jego utworzenia.
        :return:
        """
        def decode_date(code):
            cert_data = code.cert
            x509_cert = x509.load_der_x509_certificate(cert_data, default_backend())
            not_before = x509_cert.not_valid_before
            return not_before.strftime("%Y-%m-%d %H:%M:%S")

        alias_inp = input("Podaj nazwę certyfikatu ([enter] - powrót): ")
        if not alias_inp:
            clean()
            return

        try:
            found = {}
            for alias, c in keystore.certs.items():
                if alias_inp in alias:
                    found[alias] = c
            if len(list(found)) != 0:
                for alias, c in found.items():
                    print("\nZNALEZIONO: {}".format(alias))
                    print("{}DATA UTWORZENIA:{} {}\n".format(blue, reset, decode_date(c)))
                    print("-----BEGIN CERTIFICATE-----")
                    print("\r\n".join(textwrap.wrap(base64.b64encode(c.cert).decode('ascii'), 64)))
                    print("-----END CERTIFICATE-----")
                    input("\n[enter] - {}".format("wyświetl następny" if alias != list(found)[-1] else "powrót..."))
                    clean()
                return
            else:
                print("Nie znaleziono podanego aliasu.")
        except Exception as er:
            print("{}Błąd:{} {}".format(red, reset, er))
        input("\n[enter] - powrót...")
        clean()

    @clean_decor
    def delete_cert(keystore):
        alias_inp = input("Podaj nazwę certyfikatu ([enter] - powrót): ")
        try:
            if alias_inp in keystore.entries:
                del java_keystore.entries[alias_inp]

                keystore.save(ksfilefp, keystore_pwd)

                print(f"Usunięto certyfikat '{alias_inp}' z magazynu kluczy '{ksfile}'.")
                time.sleep(2)
            elif alias_inp.strip() == "":
                print(cancel)
            else:
                print(f"Nie znaleziono certyfikatu '{alias_inp}' w magazynie kluczy '{ksfile}'.")
                time.sleep(2)
        except Exception as er:
            print("{}Błąd:{} {}".format(red, reset, er))
            input("Kontynuuj...")

    choosing = True

    try:
        java_keystore = jks.KeyStore.load(ksfilefp, keystore_pwd)

        cert_count = len(java_keystore.certs)

        lsmenu = [
            f"Wyświetl wszystkie nazwy ({cert_count})",
            "Wyświetl certyfikat i datę utworzenia",
            "Usuń certyfikat z magazynu kluczy"
            ]

        while choosing:
            for lspos in lsmenu:
                print("[{}] - {}".format(lsmenu.index(lspos) + 1, lspos))
            print("\n[c] - powrót\n")
            choice = input("Wybierz opcję i potwierdź: ")

            if choice == "c":
                choosing = False
            elif choice.isdigit() and int(choice) in range(1, 4):
                choice = int(choice) - 1
                if choice == 0:
                    print_aliases(java_keystore)
                elif choice == 1:
                    print_certificate(java_keystore)
                elif choice == 2:
                    delete_cert(java_keystore)
            else:
                clean()
                print(try_again)

    except Exception as err:
        print(err)


def check_structure():
    """
    Funkcja tworząca strukturę katalogów w przypadku jej braku na hoście źródłowym.
    :return:
    """
    need_restart = False
    if not os.path.exists(datadir):
        os.mkdir(datadir)
        need_restart = True
    if not os.path.exists(ksdir):
        os.mkdir(ksdir)
        need_restart = True
    if not os.path.exists(certdir):
        os.mkdir(certdir)
        need_restart = True
    if need_restart:
        print("Utworzono strukturę katalogów. "
              "Umieść plik magazynu kluczy w folderze 'keystores' i uruchom ponownie program.")
        print("Jeżeli masz zamiar zaimportować certyfikaty, umieść je w katalogu 'certs' przed uruchomieniem programu.")
        return True


def jdk_present():
    """
    Funkcja sprawdzająca obecność Java Development Kit w hoście źródłowym.
    :return:
    """
    try:
        result = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True).split("\n")
        for line in result:
            if "openjdk version" in line:
                return True
    except Exception:
        return False


def connection_ok(host):
    """
    Healthcheck dla połączenia z hostami docelowymi.
    :param host: String -> nazwa hosta będąca kluczem parametru instancji conson.
    :return:
    """
    global error
    global conn_status
    error = ""
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(data()[host][0], data()[host][1], data()[host][2], data.unveil(data()[host][3]))

        transport = ssh.get_transport()

        if transport.is_active():
            ssh.close()
            conn_status[host] = True
            return
        else:
            ssh.close()
            conn_status[host] = False
            return
    except Exception as err:
        error = str(err)
        ssh.close()
        conn_status[host] = False
        return


@clean_decor
def select_keystore():
    """
    Funkcja menu wyboru magazynu kluczy z listy plików w folderze ./keystores
    :return:
    """
    global ksfile
    global ksdir
    global ksfilefp
    global datafile
    global datafilefp
    global setup
    global keystore_pwd
    global host_status_fresh
    choosing = True
    files = os.listdir(ksdir)

    while choosing:
        i = 0
        for file in files:
            print("[{}] - {}".format(files.index(file) + 1, file))
            i += 1

        print(separator)
        print("\n[c] - powrót\n")

        choice = input("Wybierz plik magazynu kluczy: ")
        if choice == "c":
            clean()
            print(cancel)
            ksfile = ksfile
            choosing = False
        elif choice.isdigit():
            if int(choice) in range(1, len(files) + 1):
                if ksfile == "":
                    setup = True
                else:
                    setup = False
                ksfile = files[int(choice) - 1]
                ksfilefp = os.path.join(ksdir, ksfile)
                datafile = ksfile + ".json"
                datafilefp = os.path.join(datadir, datafile)
                data.file = datafilefp
                choosing = False
                keystore_pwd = input("Wprowadź hasło do magazynu kluczy (domyślnie: changeit): ")
                keystore_pwd = "changeit" if keystore_pwd == "" else keystore_pwd
                host_status_fresh = False
            else:
                clean()
                print(try_again)
        else:
            clean()
            print(try_again)


def get_config():
    """
    Funkcja wczytująca istniejący plik konfiguracyjny przypisany do magazynu kluczy LUB tworząca pusty plik
     w formacie: <nazwa magazynu>.json
    :return:
    """
    if not os.path.exists(datafilefp):
        data.save()
    try:
        data.dump()
        data.load()
    except Exception as err:
        print(err)
        return False


@clean_decor
def salt_edit():
    global host_status_fresh
    """
    Edycja wartości soli kryptograficznej.
    :return:
    """
    new_salt = input("Wprowadź sól (domyślnie: ch4ng3M3pl3453): ")
    if new_salt == "":
        print(cancel)
        time.sleep(2)
    else:
        data.salt = new_salt
        print("{}KLUCZ ZOSTAŁ ZMIENIONY{}".format(green, reset))
        host_status_fresh = False
        time.sleep(2)



@clean_decor
def target_hosts():
    """
    Funkcja menu hostów docelowych.
    :return:
    """
    choosing = True

    @clean_decor
    def new_value(val):
        """
        Funkcja dodawania nowej wartości parametru.
        :param val: String -> wartość właściwa dla określonego parametru.
        :return:
        """
        while True:
            changed_to = input("{} :".format(val))
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
                elif "Komendy" in val:
                    commands = changed_to.split("#")
                    clean_commands = []
                    for command in commands:
                        if len(command) > 0:
                            clean_commands.append(command.strip())
                    return clean_commands
                else:
                    return changed_to

            except Exception as err:
                print(err)
                input("Kontynnuj...")

    @clean_decor
    def add_host():
        """
        Funkcja dodająca nowe hosty docelowe do pliku konfiguracyjnego przypisanego do magazynu kluczy.
        :return:
        """
        global host_status_fresh
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
        values = {vrs[vrsl[0]]: [vrs[vrsl[1]], vrs[vrsl[2]], vrs[vrsl[3]], vrs[vrsl[4]], vrs[vrsl[5]]]}
        data.create(vrs[vrsl[0]], values[vrs[vrsl[0]]])
        data.veil(vrs[vrsl[0]], 3)
        data.save()
        host_status_fresh = False
        return

    @clean_decor
    def edit_host(host_key):
        """
        Funkcja edytowania parametrów (wartości) przypisanych do hosta (klucza).
        :param host_key: String -> klucz odpowiadający przyjaznej nazwie hosta.
        :return:
        """
        global host_status_fresh
        choosing_parameter = True
        values = data()[host_key]
        while choosing_parameter:
            print(separator)
            print("Edytowany host: {}".format(host_key))
            print(separator)
            print("{}: {}".format(uni_val[0], values[0]))
            print("{}: {}".format(uni_val[1], values[1]))
            print("{}: {}".format(uni_val[2], values[2]))
            print(separator)
            print("{}: {}".format(uni_val[4], values[4]))
            print(separator)

            for opt in uni_val:
                print("[{}] - {}{}".format(uni_val.index(opt) + 1, "Zmień ", opt if opt == uni_val[0] else opt.lower()))
            print("\n[c] - powrót\n")
            parameter_choice = input("Wybierz opcję i potwierdź: ")

            if parameter_choice == "c":
                choosing_parameter = False
                clean()
            elif parameter_choice.isdigit() and int(parameter_choice) in range(1, 6):
                value[int(parameter_choice) - 1] = new_value(uni_val[int(parameter_choice) - 1])
                data.create(host_key, values)
                if int(parameter_choice) == 3:
                    data.veil(data()[host_key][3])
                host_status_fresh = False
                data.save()
                clean()
                return

    @clean_decor
    def delete_host(host_key):
        """
        Usuń dane hosta z konfiguracji.
        :param host_key: String -> klucz odpowiadający przyjaznej nazwie hosta.
        :return:
        """
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
            print("Uwaga: ustaw wartość soli przed definiowaniem hostów.")
            print(separator)

        if len(data()) != 0:
            print("[{}-{}] - wybierz hosta do edycji".format(1, len(data())))
            print("[d] + [{}-{}] - usuń hosta".format(1, len(data())))
        print("[a] - dodaj nowego hosta")
        print("[s] - zmień sól")
        print("\n[c] - powrót\n")
        choice = input("Wybierz opcję i potwierdź: ")
        if choice == "c":
            clean()
            print(cancel)
            return
        if choice == "s":
            salt_edit()
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
                clean()
                print(try_again)
        elif choice.isdigit() and int(choice) in range(1, len(data()) + 1):
            edit_host(list(data())[int(choice) - 1])
        else:
            clean()
            print(try_again)


def refresh_all_statuses(outdated=False):
    global host_status_fresh
    if outdated:
        host_status_fresh = False
    if not host_status_fresh:
        host_status_fresh = True
        print("Odpytywanie hostów...", end="", flush=True)
        time.sleep(1)
        for key in list(data()):
            connection_ok(key)
        print("\r" + " " * 30, end="", flush=True)
        print("")
    return


@clean_decor
def cert_into_ks():

    def proceed():
        try:
            i = 0
            for file in os.listdir(certdir):
                try:
                    if file.split(".")[1] == "crt":
                        keystore = jks.KeyStore.load(ksfilefp, keystore_pwd)
                        alias = file.split(".")[0]
                        with open(os.path.join(certdir, file), 'rb') as crt_file:
                            crt_data = crt_file.read()
                        cert = x509.load_pem_x509_certificate(crt_data, default_backend())

                        trusted_cert_entry = jks.TrustedCertEntry.new(
                            alias=alias, cert=cert.public_bytes(serialization.Encoding.DER)
                        )
                        keystore.entries[alias] = trusted_cert_entry

                        keystore.save(ksfilefp, keystore_pwd)
                        i += 1
                except IndexError:
                    print("{}Błąd:{} Brak plików .crt w katalogu './certs'.".format(red, reset))
                    print(cancel)
                    time.sleep(2)
                except Exception as err:
                    print("{}Błąd: {}{}".format(red, reset, err))
                    input("Kontynuuj...")
            if i > 0:
                no_wez_odmien = ["certyfikat", "certyfikaty", "certyfikatów"]
                if i == 1:
                    odmiana = no_wez_odmien[0]
                elif i == 2:
                    odmiana = no_wez_odmien[1]
                else:
                    odmiana = no_wez_odmien[2]
                print("{}SUKCES:{} zaimportowano {} {}}.".format(green, reset, i, odmiana))
                time.sleep(2)
        except Exception as err:
            print("{}Błąd: {}{}".format(red, reset, err))
            input("Kontynuuj...")

    warn = """
#############
#   UWAGA   #
#############

Zostaną zaimportowane wszystkie pliki .crt znajdujące się w katalogu './certs'.
Kontynuować?
"""

    print(warn)
    choosing = True
    while choosing:
        choice = input("[t/n] - domyślnie [n]: ")

        if choice == "" or choice.lower() == "n":
            print(cancel)
            choosing = False
        elif choice.lower() == "t":
            if len(os.listdir(certdir)) != 0:
                proceed()
            else:
                print("Brak plików certyfikatów w katalogu ./certs \n{}".format(cancel))
                time.sleep(2)
            choosing = False
        else:
            print(try_again)


# Narzędzia formatowania tekstu
green = "\033[92m"
red = "\033[91m"
blue = "\033[94m"
yellow = "\033[93m"
reset = "\033[0m"
welcome = "{} v{} by {}".format(name, version, author)
separator = "-" * len(welcome)
cancel = "\n{}POWRÓT...{}".format(blue,  reset)
try_again = "\n{}{}SPRÓBUJ PONOWNIE...{}".format(clean(), red, reset)


# Menu główne
if check_structure():
    exit()

menu = ["Wybierz plik magazynu kluczy"]
menu_full = {
    "Wyświetl zawartość magazynu kluczy": ls_ks,
    "Zaimportuj certyfikaty do magazynu kluczy": cert_into_ks,
    "Wykonaj zdalną aktualizację magazynów kluczy": up_ks,
    "Wybierz plik magazynu kluczy": select_keystore,
    "Wyeksportuj i użyj lokalnego magazynu kluczy": share_ks,
    "Hosty docelowe": target_hosts,
    "Odśwież status połączenia": refresh_all_statuses,
    "Zmień sól": salt_edit
}

# Sprawdź, czy magazyn kluczy został wybrany. PRAWDA: Wyświetl nazwę pliku magazynu kluczy.
running = True
while running:
    clean()
    if ksfile != "":
        print("{}OPERUJESZ NA PLIKU: {}{}".format(green, ksfile, reset))
        get_config()

        if setup:
            menu.insert(0, list(menu_full)[0])
            menu.insert(3, list(menu_full)[1])
            menu.insert(4, list(menu_full)[2])
            menu.insert(5, list(menu_full)[5])
            menu.insert(6, list(menu_full)[7])
            setup = False
    else:
        print("\n{}WYBIERZ MAGAZYN KLUCZY{}\n".format(red, reset))
        if jdk_present():
            if list(menu_full)[4] not in menu:
                menu.insert(2, list(menu_full)[4])


# Sprawdź, czy zdefiniowane są hosty docelowe w pliku konfiguracyjnym. PRAWDA: wyświetl status połączenia z hostami.
    if len(list(data())) > 0:
        refresh_all_statuses()
        print("\nSTATUS POŁĄCZENIA:\n")
        for k in list(data()):
            print("{}{} {} {}{}".format(green if conn_status[k] else red,
                                        k, "-" if len(error) != 0 else "", error, reset))

    print("\n{}".format(separator))
    for pos in menu:
        print("[{}] - {}".format(menu.index(pos) + 1, pos))
    if len(list(data())) > 0:
        print(f"\n[r] - {list(menu_full)[6]}")
    print("\n[q] - Zakończ")

    u_in = input("\nWybierz opcję, [Enter] zatwierdza: ")
    try:
        if u_in.isalpha() and u_in.lower() == "q":
            clean(True)
            exit()
        elif u_in.isalpha() and u_in.lower() == "r":
            refresh_all_statuses(True)
        elif u_in.isdigit() and int(u_in) <= 0:
            raise Exception("input less or equal to 0")
        elif menu[int(u_in) - 1] == list(menu_full)[6]:
            menu_full[menu[int(u_in) - 1]](True)
        else:
            menu_full[menu[int(u_in) - 1]]()
    except Exception:
        clean()
        print(try_again)
