CertUp
-----------------------------------------------------------------------------------------------------------------------

Program do obsługi certyfikatów SSL w magazynach Java KeyStore na wielu zdalnych hostach docelowych.
Umożliwia odczyt i modyfikację magazynu kluczy JKS, a jego głównym zamysłem jest modyfikacja magazynu cacerts.
Dodatkowo, umożliwia transfer plików PKCS (.p12) oraz przeniesienie ich do określonego katalogu na hoście docelowym,
a także zdalne wykonanie poleceń.
Obsługa za pomocą tekstowego interfejsu użytkownika (TUI).

Wymagania:

    pip install pyjks cryptography conson paramiko

Do modyfikacji na hoście źródłowym wykorzystuje moduł pyjks wraz z modułem cryptography. 
Modyfikacja na hostach zdalnych odbywa się natywnie poprzez wykonywanie komend programu Keytool za pomocą modułu subprocess.

Wykorzystuje moduł conson do bezpiecznego przechowywania konfiguracji w plikach json i paramiko do nawiązywania połączeń.

Funkcjonalności:

    -eksport istniejącego na hoście źródłowym magazynu kluczy JKS do programu (wymaga JDK),
    -modyfikacja magazynu kluczy JKS,
    -generowanie certyfikatów SSL self-signed (klucz, certyfikat, PKCS12) (wymaga openssl),
    -wyświetlanie aliasów, dat utworzenia, treści certyfikatów,
    -importowanie certyfikatów do keystore,
    -przesyłanie magazynów JKS i PKCS do hostów zdalnych za pomocą SSH,
    -weryfikacja przesłanych plików poprzez porównanie hashów MD5,
    -przechowywanie konfiguracji hostów zdalnych przypisanych do danego magazynu kluczy,
    -bezpieczne przechowywanie haseł do hostów zdalnych (szyfrowanie SHA-256, przypisanie pliku konfiguracyjnego do hosta źródłowego, możliwość zastosowania soli).

Działanie:

Pierwsze uruchomienie programu utworzy strukturę katalogów a następnie wymusi na użytkowniku ponowne uruchomienie.

    ./configs            # Katalog plików konfiguracyjnych przechowujących dane hostów,
    ./keystores          # Katalog magazynów kluczy, na których będziemy wykonywać operacje,
    ./certs              # Katalog przechowujący certyfikaty oraz pliki PKCS. Będą tworzone podkatalogi <nazwa keystore>_certs w momencie wybrania certyfikatu z pozycji menu.
    ./certs/domains.cnf  # Katalog dla plików <alias>.cnf celem generowania certyfikatów self-signed (klucz, certyfikat, PKCS12).

Przy kolejnym uruchomieniu pojawi się menu wyboru magazynu kluczy. Jeżeli w folderze ./keystores nie ma żadnego magazynu a program wykryje instancję JDK w systemie, 
umożliwi on wyeksportowanie do tego katalogu oryginalnego magazynu kluczy cacerts i nadanie mu przyjaznej nazwy (dla celów identyfikacji). 
Jeżeli nie będzie w stanie zlokalizować magazynu, poprosi o wprowadzenie ścieżki do pliku cacerts. 

Wybranie magazynu kluczy rozszerzy widziane przez nas menu. Oprócz opcji wyboru magazynu kluczy/eksportu i wyświetlenia nazwy magazynu kluczy a także automatycznego sprawdzania dostępności zdefiniowanych hostów, pojawią się dodatkowe funkcje:

    Wyświetl zawartość magazynu kluczy                    # Pozwala na przeglądanie aliasów znajdujących się w magazynie kluczy, a także wyświetlanie ich certyfikatów bądź usuwanie ich z magazynu,
    
    Zaimportuj certyfikaty do magazynu kluczy             # Importuje wszystkie pliki .crt z podkatalogu <nazwa keystore>_certs do wybranego magazynu kluczy,
    
    Wygeneruj nowe certyfikaty self-signed                # WYMAGA OPENSSL: pozwala generować certyfikaty self-signed. wymaga co najmniej jednego pliku <alias>.cnf w katalogu ./certs/domains_cnf.
                                                                            klucz, certyfikat oraz magazyn .p12 zostaną umieszczone w ./certs/<nazwa magazynu kluczy>_certs,
    
    Wybierz plik magazynu kluczy                          # Pozwala na zmianę magazynu, na którym operujemy,
    
    Wyeksportuj i użyj lokalnego magazynu kluczy          # WYMAGA JDK:  Pozwala na eksport pliku cacerts do katalogu ./keystores i nadanie mu przyjaznej nazwy,
    
    Wykonaj zdalną aktualizację magazynów kluczy          # JEŻELI MAMY ZDEFINIOWANY CO NAJMNIEJ 1 HOST DOCELOWY: Pozwala na przesłanie na hosta zdalnego magazynu kluczy i zaimportowanie go, 
                                                                                                                  a także przesłanie pliku PKCS12 i umieszczenie go w predefiniowanym przez nas
                                                                                                                  katalogu.
    
    Hosty docelowe                                        # Umożliwia modyfikację (dodawanie, usuwanie, edycję) zdalnych hostów docelowych. te hosty przypisane będą do obecnie wybranego magazynu kluczy
                                                            i na nie ten magazyn zostanie przesłany i zaimportowany (wraz z magazynami PKCS jeżeli takie istnieją).
                                                            
    Zmień sól                                             # Pozwala na zmianę soli kryptograficznej wykorzystywanej w szyfrowaniu haseł w plikach.json 
                                                            UWAGA: zmiana soli po zdefiniowaniu hostów uniemożliwi połączenie z nimi. Jeżeli chcemy wzmocnić zabezpieczenie naszych danych 
                                                            w plikach konfiguracyjnych, należy to zrobić przed definiowaniem hostów przypisanych do danego magazynu kluczy.

    [r] - Odśwież status połączenia                       # Tylko jeśli mamy zdefiniowanego co najmniej jednego hosta docelowego - ponownie odpyta o dostępność każdego zdefiniowanego hosta docelowego.

    [q] - Zakończ                                         # Kończy pracę programu.



