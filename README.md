CertUp
-----------------------------------------------------------------------------------------------------------------------

CertUp is a program for managing Java KeyStore (JKS) SSL certificates on multiple remote hosts. It enables reading 
and modification of JKS, primarily for handling the cacerts keystore. 
Additionally, it allows for PKCS (.p12) file transfer to a remote directory and remote command execution.

The program operates through a text-based user interface (TUI).

Requirements:

    pip install pyjks cryptography conson paramiko

Modification on the source host uses the pyjks module along with the cryptography module. 
Modification on remote hosts occurs natively through the execution of Keytool commands using the subprocess module.

It utilizes the conson module for secure configuration storage in JSON files and paramiko for establishing connections.

Features:

    - Export of an existing JKS keystore from the source host (requires JDK),
    - Modification of JKS keystore,
    - Generation of self-signed SSL certificates (key, certificate, PKCS12) (requires openssl),
    - Displaying aliases, creation dates, and certificate contents,
    - Importing certificates into the keystore,
    - Transfer of JKS and PKCS stores to remote hosts via SSH,
    - Verification of transferred files through MD5 hash comparison,
    - Storage of configurations for remote hosts assigned to a specific keystore,
    - Secure storage of passwords for remote hosts (SHA-256 encryption, assignment of a configuration file 
        to the source host, option to apply cryptographic salt).


Operation:

The first program run creates a directory structure and then forces the user to restart.

    ./configs            # Directory for configuration files storing host data,
    ./keystores          # Directory for keystore operations,
    ./certs              # Directory for storing certificates and PKCS files. Subdirectories <keystore name>_certs will be created when selecting a certificate from the menu.
    ./certs/domains.cnf  # Directory for <alias>.cnf files for generating self-signed certificates (key, certificate, PKCS12).


On subsequent runs, a keystore selection menu will appear. If there is no keystore in the ./keystores folder 
and the program detects a JDK instance in the system, it allows exporting the original cacerts keystore to this directory 
and giving it a friendly name (for identification purposes). If it cannot locate the keystore, it will prompt 
for the path to the cacerts file.

Selecting a keystore will expand the menu. In addition to the options for selecting a keystore/exporting and displaying 
the keystore name and automatically checking the availability of defined hosts, additional functions will appear:

    Wyświetl zawartość magazynu kluczy

Allows browsing aliases in the keystore, displaying their certificates, or removing them from the keystore,
    
    Zaimportuj certyfikaty do magazynu kluczy
    
Imports all .crt files from the <keystore name>_certs subdirectory into the selected keystore,
    
    Wygeneruj nowe certyfikaty self-signed

REQUIRES OPENSSL: allows generating self-signed certificates. 
Requires at least one <alias>.cnf file in the ./certs/domains_cnf directory.
The key, certificate, and .p12 store will be placed in ./certs/<keystore name>_certs,
    
    Wybierz plik magazynu kluczy
    
Allows changing the keystore on which you operate,
    
    Wyeksportuj i użyj lokalnego magazynu kluczy

REQUIRES JDK: Allows exporting the cacerts file to the ./keystores directory and giving it a friendly name,
    
    Wykonaj zdalną aktualizację magazynów kluczy

IF AT LEAST 1 TARGET HOST IS DEFINED: Allows transferring the keystore to a remote host and importing it, 
                                      as well as transferring the PKCS12 file and placing it in a directory 
                                      predefined by us.
    
    Hosty docelowe

Allows modification (addition, removal, editing) of remote target hosts. These hosts will be assigned to the 
currently selected keystore, and the keystore will be transferred and imported (along with PKCS stores if they exist).
                                                            
    Zmień sól

Allows changing the cryptographic salt used in password encryption in JSON files.
WARNING: Changing the salt after defining hosts will prevent connection to them. 
If you want to strengthen the security of your data in configuration files, 
it should be done BEFORE defining hosts assigned to a specific keystore.

    Odśwież status połączenia

IF AT LEAST 1 TARGET HOST IS DEFINED: Requeries the availability of each defined target host.

    Zakończ

Ends the program's operation.



