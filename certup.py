import os
import subprocess
import shutil
import time
import paramiko
from conson import Conson
import jks


# Informacje
name = "CertUp"
version = 1.0
author = "PG/DASiUS"    # https://github.com/pgabrys94

# Zmienne globalne:
certdir = os.path.join(os.getcwd(), "certs")
certfile = ""
certfilefp = None
datadir = os.path.join(os.getcwd(), "configs")
datafile = None
datafilefp = ""
setup = False
error = ""  # pozwala na wyświetlenie błędu przy nieosiągalnym hoście docelowym.
keystore_pwd = ""
uni_val = ["IP", "Port", "Login", "Hasło", "Komendy"]
conn_status = {}

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
        self.commands = [command.strip() for command in command_list.split("#") if command]
        self.terminal = paramiko.SSHClient()
        self.path = os.path.join("/", "home", self.login, "certup") if self.login != "root"\
            else os.path.join("/", "root", "certup")
        self.backup_path = os.path.join(self.path, "backup")
        self.verbose = verbose
        self.file = "cacerts"

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
        command = (f"keytool -importkeystore -deststorepass {destpwd} -trustcacerts -srckeystore"
                   f" {os.path.join(self.path, self.file)} -srcstorepass {srcpwd} -noprompt")
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
            sftp.put(file, os.path.join(self.path, self.file))
            sftp.close()
            if self.verbose:
                print("{}Wysłano: {}:{}{}".format(green, self.ip, os.path.join(self.path, self.file), reset))
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
def up_certs():
    def execute(target):
        target.connect()
        target.create_tree()
        target.upload(certfilefp)
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
            print("[c] - powrót\n")
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
def share_cert():
    """
    Funkcja eksportu magazynu kluczy z hosta źródłowego.
    :return:
    """

    def locate_java_certs():
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

    global certfile
    global certdir
    global certfilefp
    global datafile
    global datafilefp
    global datadir
    global setup
    global keystore_pwd

    certfile = input("Wprowadź przyjazną nazwę dla pliku magazynu kluczy: ")
    keystore_pwd = input("Wprowadź hasło do magazynu kluczy (domyślnie: changeit): ")
    keystore_pwd = "changeit" if keystore_pwd == "" else keystore_pwd

    certfilefp = os.path.join(certdir, certfile)
    datafile = certfile + ".json"
    datafilefp = os.path.join(datadir, datafile)
    data.file = datafilefp
    setup = True
    try:
        cacfp = locate_java_certs()
        if cacfp is False:
            print("is false")
            cacfp = r"{}".format(input("Wprowadź ścieżkę absolutną do magazynu kluczy (cacerts): "))

        if not os.path.exists(cacfp):
            raise Exception("Podany magazyn kluczy nie istnieje.")
        else:
            shutil.copy(cacfp, certfilefp)

        data.save()
    except Exception as err:
        print(err)


@clean_decor
def ls_certs():
    """
    Funkcja menu wyświetlania zawartości magazynu kluczy.
    :return:
    """

    def print_aliases(output):
        """
        Wyświetl wszystkie aliasy w magazynie kluczy.
        :param output: Rezultat zapytania o zawartość magazynu w rfc.
        :return:
        """
        result = ""
        for ln in output.split("\n"):
            if "alias name" in ln.lower():
                result += ln[ln.index(":") + 1:]
        print(result.replace(" ", " | "))
        input("\n[enter] - powrót...")
        clean()

    def print_certdate(output):
        """
        Wyświetl datę zaimportowania wskazanego certyfikatu do obecnego magazynu kluczy.
        :param output: Rezultat zapytania o zawartość magazynu BEZ rfc.
        :return:
        """
        uin = input("Podaj alias certyfikatu ([enter] - powrót): ")

        if len(uin) == 0:
            clean()
            return
        elif len(uin) > 0:
            for ln in output.split("\n"):
                if uin in ln.lower():
                    print(ln.split(",")[1].strip())
                    input("\n[enter] - powrót...")
                    clean()
                    return

        if len(uin) > 0:
            print("Nie znaleziono podanego aliasu.")
            input("\n[enter] - powrót...")
            clean()

    def print_certificate():
        """
        Wyświetl klucz certyfikatu.
        :return:
        """
        try:
            uin = input("Podaj nazwę certyfikatu ([enter] - powrót): ")

            if len(uin) > 0:
                try:
                    cert_query = subprocess.check_output(["keytool", "-list", "-keystore", f"{certfilefp}",
                                                          "-storepass", f"{keystore_pwd}", "-alias", f"{uin}", "-rfc"],
                                                         text=True)

                    i = 3
                    if uin in cert_query.split("\n")[0]:
                        for ln in cert_query.split("\n"):
                            i -= 1
                            if i <= 0:
                                print(ln)
                        input("\n[enter] - powrót...")
                        clean()
                        return
                except Exception:
                    print("Nie znaleziono podanego aliasu.")
                    input("\n[enter] - powrót...")
                    clean()
                    return
            else:
                clean()
                return
        except Exception:
            clean()
            print(try_again)

    global keystore_pwd
    global certfilefp
    choosing = True
    cert_count = 0

    try:

        query = subprocess.check_output(["keytool", "-list", "-keystore", f"{certfilefp}", "-storepass",
                                         f"{keystore_pwd}", "-rfc"], text=True)

        simple_query = subprocess.check_output(["keytool", "-list", "-keystore", f"{certfilefp}",
                                                "-storepass", f"{keystore_pwd}"], text=True)

        for line in query.split("\n"):
            if "contains" in line:
                cert_count = int(line.split(" ")[3])

        lsmenu = [f"Wyświetl wszystkie nazwy ({cert_count})", "Wyświetl datę utworzenia certyfikatu",
                  "Wyświetl certyfikat"]

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
                    print_aliases(query)
                elif choice == 1:
                    print_certdate(simple_query)
                elif choice == 2:
                    print_certificate()
            else:
                clean()
                print(try_again)

    except Exception as err:
        print(err)

###############################Funkcja eksperymentalna, wyklucza potrzebę posiadania jdk na hoście źródłowym############
@clean_decor
def ls_certs_pyjks():
    global keystore_pwd
    global certfilefp

    def print_aliases(keystore):
        result = ""
        column = 2
        width = 80
        for i, alias in enumerate(list(keystore.certs), start=1):
            result += alias
            formatted = "{:<{}}".format(alias, width)
            print(formatted, end="\n" if i % column == 0 else " ")

    def print_certdate(keystore):
        alias = input("Podaj alias certyfikatu ([enter] - powrót): ")
        if not alias:
            clean()
            return
        try:
            cert_entry = keystore.private_keys.get(alias)
            if cert_entry:
                print(cert_entry.cert.creation_date)
            else:
                print("Nie znaleziono podanego aliasu.")
        except Exception:
            print("Wystąpił błąd.")
        input("\n[enter] - powrót...")
        clean()

    def print_certificate(keystore):
        alias = input("Podaj nazwę certyfikatu ([enter] - powrót): ")
        if not alias:
            clean()
            return
        try:
            cert_entry = keystore.private_keys.get(alias)
            if cert_entry:
                print(cert_entry.cert)
            else:
                print("Nie znaleziono podanego aliasu.")
        except Exception:
            print("Wystąpił błąd.")
        input("\n[enter] - powrót...")
        clean()

    choosing = True

    try:
        #with open(certfilefp, 'rb') as keystore_file:
        keystore = jks.KeyStore.load(certfilefp, keystore_pwd)

        cert_count = len(keystore.certs)

        lsmenu = [f"Wyświetl wszystkie nazwy ({cert_count})", "Wyświetl datę utworzenia certyfikatu",
                  "Wyświetl certyfikat"]

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
                    print_aliases(keystore)
                elif choice == 1:
                    print_certdate(keystore)
                elif choice == 2:
                    print_certificate(keystore)
            else:
                clean()
                print(try_again)

    except Exception as err:
        print(err)
########################################################################################################################
def check_structure():
    """
    Funkcja tworząca strukturę katalogów w przypadku jej braku na hoście źródłowym.
    :return:
    """
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
    Funkcja menu wyboru magazynu kluczy z listy plików w folderze ./certs
    :return:
    """
    global certfile
    global certdir
    global certfilefp
    global datafile
    global datafilefp
    global setup
    global keystore_pwd
    choosing = True
    files = os.listdir(certdir)

    while choosing:
        i = 0
        for file in files:
            print("[{}] - {}".format(files.index(file) + 1, file))
            i += 1

        print(separator)
        print("[c] - powrót\n")

        choice = input("Wybierz plik magazynu kluczy: ")
        if choice == "c":
            clean()
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
                keystore_pwd = input("Wprowadź hasło do magazynu kluczy (domyślnie: changeit): ")
                keystore_pwd = "changeit" if keystore_pwd == "" else keystore_pwd
            else:
                clean()
                print(try_again)
        else:
            clean()
            print(try_again)


def get_config():
    """
    Funkcja wczytująca istniejący plik konfiguracyjny przypisany do certyfikatu LUB tworząca pusty plik
     w formacie: <nazwa certyfikatu>.json
    :return:
    """
    if not os.path.exists(datafilefp):
        data.save()
    else:
        try:
            data.load()
        except Exception as err:
            print(err)
            return False


def salt_edit():
    """
    Edycja wartości soli kryptograficznej.
    :return:
    """
    new_salt = input("Wprowadź sól (domyślnie: ch4ng3M3pl3453): ")
    if new_salt == "":
        clean()
        print(cancel)
    else:
        data.salt = new_salt
        return "{}KLUCZ ZOSTAŁ ZMIENIONY{}".format(green, reset)


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
        """
        Funkcja dodająca nowe hosty docelowe do pliku konfiguracyjnego przypisanego do magazynu kluczy.
        :return:
        """
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

    @clean_decor
    def edit_host(host_key):
        """
        Funkcja edytowania parametrów (wartości) przypisanych do hosta (klucza).
        :param host_key: String -> klucz odpowiadający przyjaznej nazwie hosta.
        :return:
        """
        choosing_parameter = True
        changed = False
        values = data()[host_key]

        while choosing_parameter:
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
            parameter_choice = input("Wybierz opcję i potwierdź: ")

            if parameter_choice == "c":
                if changed:
                    data.save()
                choosing_parameter = False
                clean()
            elif parameter_choice.isdigit() and int(parameter_choice) in range(1, 6):
                changed = True
                value[int(parameter_choice) - 1] = new_value(uni_val[int(parameter_choice) - 1])
                data.create(host_key, values)
                data.veil(data()[host_key][3])
                clean()

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
        print("[c] - powrót\n")
        choice = input("Wybierz opcję i potwierdź: ")
        if choice == "c":
            clean()
            print(cancel)
            choosing = False
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


def refresh_all_statuses():
    for key in list(data()):
        connection_ok(key)
    return


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
    "Wyświetl certyfikaty": ls_certs_pyjks,
    "Wykonaj zdalną aktualizację magazynów kluczy": up_certs,
    "Wybierz plik magazynu kluczy": select_keystore,
    "Wyeksportuj i użyj lokalnego magazynu kluczy": share_cert,
    "Hosty docelowe": target_hosts,
    "Zmień sól": salt_edit,
    "Odśwież status połączenia" : refresh_all_statuses
}

# Sprawdź, czy magazyn kluczy został wybrany. PRAWDA: Wyświetl nazwę pliku magazynu kluczy.
running = True
while running:
    clean()
    if certfile != "":
        print("{}OPERUJESZ NA PLIKU: {}{}".format(green, certfile, reset))
        get_config()
        if setup:
            try:
                menu.pop(menu.index(list(menu_full)[3]))
            except Exception:
                pass
            menu.insert(0, list(menu_full)[0])
            menu.insert(1, list(menu_full)[1])
            menu.insert(3, list(menu_full)[4])
            menu.insert(4, list(menu_full)[5])
        setup = False
    else:
        print("\n{}WYBIERZ MAGAZYN KLUCZY{}\n".format(red, reset))
        if jdk_present():
            if list(menu_full)[3] not in menu:
                menu.insert(1, list(menu_full)[3])


# Sprawdź, czy zdefiniowane są hosty docelowe w pliku konfiguracyjnym. PRAWDA: wyświetl status połączenia z hostami.
    if len(data()) != 0:
        print("Odpytywanie hostów...", end="", flush=True)
        refresh_all_statuses()
        print("\r" + " " * 30, end="", flush=True)
        print("\nSTATUS POŁĄCZENIA:\n")
        for k in list(data()):
            print("{}{} {} {}{}".format(green if conn_status[k] else red,
                                        k, "-" if len(error) != 0 else "", error, reset))

    print("\n{}".format(separator))
    for pos in menu:
        print("[{}] - {}".format(menu.index(pos) + 1, pos))
    print("\n[q] - Zakończ")

    u_in = input("\nWybierz opcję, [Enter] zatwierdza: ")
    try:
        if u_in.isalpha() and u_in.lower() == "q":
            clean(True)
            exit()
        elif u_in.isdigit() and int(u_in) <= 0:
            raise Exception("input less or equal to 0")
        else:
            menu_full[menu[int(u_in) - 1]]()
    except Exception:
        clean()
        print(try_again)
