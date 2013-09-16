statcode
========

Statcode is a tool to classify all the files contained in a directory tree. It was specifically thought to analyze a source tree, but it can parse every directory and classify any kind of files.
Statcode is configurable, so that new file types can easily be added. 

In order to classify a file, currently statcode analyzes:
* the file name (extension or pattern)
* the file content (only the shebang line)
So currently statcode does not really classify files bases on generic content. In the future it should be able to detect the language of a file by searching known patterns in its content.

File types are collected in categories (for instance, 'language', 'data', 'audio', ...; 'c++' and 'python' are filetypes belonging to the 'language' category, while 'mp3' is an 'audio' filetype').

Each category can be collapsed (in this case statcode shows the cumulative data for all the filetypes belonging to that category) or hidden (in this case the category is not shown).

```shell
$ statcode Configment 
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #FILES       #LINES       #BYTES
tool                                         4           52         1668
shell            bash                        1          173         3918
language         python                      1          429        13699
document                                    14         2115        60668
language         c++                       176        27809       909136
                 TOTAL                     196        30578       989089

$ statcode Configment --collapse language
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #FILES       #LINES       #BYTES
tool                                         4           52         1668
shell            bash                        1          173         3918
document                                    14         2115        60668
language                                   177        28238       922835
                 TOTAL                     196        30578       989089

$ statcode Configment --collapse language --hide tool --hide shell --expand 'doc*'
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #FILES       #LINES       #BYTES
document         config                      3           53          976
document         text                       10          922        28413
document         markdown                    1         1140        31279
language                                   177        28238       922835
                 TOTAL                     191        30353       983503

```

Patterns can be used (like in shell file globbing). A '!' before the pattern negates it.

```shell
$ statcode Configment --hide '!language'
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #FILES       #LINES       #BYTES
language         python                      1          429        13699
language         c++                       176        27809       909136
                 TOTAL                     177        28238       922835

```

It is possible to select only specific filetypes in output.

```shell
$ statcode Configment --hide '!language' --select-filetypes python
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #FILES       #LINES       #BYTES
language         python                      1          429        13699
                 TOTAL                       1          429        13699

```

It is also possible to show information about each file of a specific filetype.

```shell
$ statcode Configment --hide '!language' --list-files python
=== Project[/home/simone/Programs/Programming/Configment]             
CATEGORY         FILETYPE               #LINES       #BYTES FILENAME
language         python                    429        13699 .../Configment/md/make_readme_md
                 TOTAL                     429        13699 

```
