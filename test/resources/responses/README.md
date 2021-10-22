You can download html files with
```shell
wget -O SPIDER_NAME/NAMING_SCHEMA THE_URL_DOT_COM
```

For the naming schema, it depends on the spider:
* **data_monitor**  
DDMMYYYY.html
* **search_results**  
  CONTEXT_INDEX_ITEMSONPAGE_DDMMYYYY.html
* **details**  
  * abgeschlossene Projekte:
    CONTEXT_ID_LANGUAGE_finished_DDMMYYYY.html
  * alle anderen:  
    CONTEXT_ID_LANGUAGE_DDMMYYYY.html
