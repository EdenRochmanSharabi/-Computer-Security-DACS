# Requirements
* We are using ssl protocol for secure data transferring. Please be sure that you have downloaded latest version of openSSL.<br>
    You can download it here: https://slproweb.com/products/Win32OpenSSL.html<br>
    Make sure to add path to /bin/ to your path environment variable.(IDE restart may be needed, also it may be so that you will have to
    add it both to your user and global path variable)
* Install all dependencies by running
```
pip install -r requirements.txt
```

# How to run the system:
1. Launch [server.py](server.py) and wait for a few seconds
2. Configure all client configs. Fill them with data you want to use. Configs can be found [here](configs)
3. Launch [client.py](client.py)

# Project information
## Password requirements
* At least one lower case character
* At least one upper case character
* At least one digit
* 8 <= Length <= 50

## ID requirements
* Only latin alphabet
* Digits are allowed
* 3 <= Length <= 50

## Action requirements
* INCREASE - increases counter
* DECREASE - decreases counter
* Possible values: positive integers(not astronomically large, max specified int value will be used in this case)
* Delay: larger than 0 and smaller than 10(to avoid long wait times). If requirement is violated default value(=1) 
will be used

## Debug mode
There is DEBUG variable in server.py. Setting this variable to True allows server to log client id's and other sensitive
information. This is only for testing purposes and should be excluded in production of course
Default value is False