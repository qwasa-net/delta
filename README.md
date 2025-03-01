# delta — yet another answering machine

## a.k.a. Сверхъестественный интеллект или ёщё одна программа автоответчик

<img src="misc/delta-icon-512x512.png" alt="imperfect delta logo" width="200" />

Super simple implementation of context-free regexps patterns matching algorithm.\
No Machine Learning Algorithms or Neural Networks were harmed in the process.

-------

### Usage example:

```python
    import delta
    d = delta.Delta()
    d.load_dictionary('dictionary.xml')
    output = d.parse('hello, world!')
    print(output)
```
-------

### Dictionary format:

```xml
<dictionary version="1.0">

    <!-- dictionary is a set of entries, each with patterns and answers -->
    <entry>

        <!-- any pattern must match -->
        <patterns>
            <pattern>hello</pattern>
            <pattern>good morning</pattern>
        </patterns>

        <!-- answer for the matched entry is selected RANDOMLY -->
        <answers>
            <answer>hi!</answer>
            <answer>hello</answer>
        </answers>

    </entry>

</dictionary>
```

Directory `data` contains some sample dictionaries, e.g. `dictionary-test.xml`.

### Live demo:
tg://delta_beta_bot