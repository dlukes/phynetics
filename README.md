# Overview

A python module for generating rule-based phonetic transcription of Czech based
on input text. Still highly experimental. Please ask if interested in details or
additional features.

# Usage

```python
import cstrans as t

sent = "Byl pozdní večer, první máj..."
trans = t.Transcript(sent)
print(trans.fon)

# >>> bil pozdňí večer , prvňí máj ...
```

# Version

v0.0.1

# License

Copyright © 2015 David Lukeš

Distributed under the GNU General Public License v3.
