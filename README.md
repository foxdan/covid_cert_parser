# covid_cert_parser
Simple Python script for parsing EU Digital Covid Certificates

```shell
$ pipenv install
$ pipenv run python ./decode.py --test
# Identity Info
SURNAME(S):	Bloggs
FORENAME(S):	Jane
ID SURNAME(S):	BLOGGS
ID FORENAME(S):	JANE
DOB:		1988-06-07

# Vaccine Info
Doses (rcvd/rqrd):	1/2
Latest Dose Date:	2021-05-06
Manufacturer:		Biontech Manufacturing GmbH
Product:		Comirnaty

#Cert Info:
Issue Date:	Mon, 07 Jun 2021 07:46:28 +0000
Expire Date:	Mon, 14 Jun 2021 09:00:00 +0000
$ get_qr_data_cmd | pipenv run python ./decode.py
```
