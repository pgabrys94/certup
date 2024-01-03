CertUp
-----------------------------------------------------------------------------------------------------------------------

Program do obsługi certyfikatów SSL w magazynach Java KeyStore na wielu zdalnych hostach docelowych.
Umożliwia odczyt i modyfikację magazynu kluczy JKS, a jego głównym zamysłem jest modyfikacja magazynu cacerts.
Dodatkowo, umożliwia transfer plików PKCS (.p12) oraz przeniesienie ich do określonego katalogu na hoście docelowym,
a także zdalne wykonanie poleceń.
Obsługa za pomocą interfejsu linii komend.

Wymagania:

    pip install pyjks cryptography conson paramiko

Do modyfikacji na hoście źródłowym wykorzystuje moduł pyjks wraz z modułem cryptography. 
Modyfikacja na hostach zdalnych odbywa się natywnie poprzez wykonywanie komend programu Keytool za pomocą modułu subprocess.

Wykorzystuje moduł conson do bezpiecznego przechowywania konfiguracji w plikach json i paramiko do nawiązywania połączeń.
