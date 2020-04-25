<!-- 
author: Erik O'Shaughnessy
date: 26 Apr 2020
-->

# Python Packaging Demystified

Often then next question from a new Python programmer is:

```HUMAN

"How do I make my awesome Python thingy available to other people?"

```

To answer this question, we first need to learn a little bit about the
Python ecosystem and how to structure our code to share it efficiently
with the world.


## Here Comes Another History Lesson

[tl;dr][#Why-Python-is-Cooler-Than-Other-Language-Ecosystems] - life
was hard on the Internet before Python.

In the days of yore, when you needed a library to extend the
functionality of your program, you only had a few choices. First you
could write it yourself. Another alternative was maybe your operating
system provided it.  Best and worst of all, you could look for it on
the [Internet][27]. If you found something close, you would need to
get it running on the magic combination of your hardware, compiler
and operating system.

Finding things with the early Internet was difficult; it took
patience, hard-won experience and luck. You had to follow your
favorite topic in [USENET][21] news groups, exchange [email][27] with
other developers/students/afficiandos, hang out in [IRC][22] chats, or
maybe hear about the latest coolest thing while hacking out your
semester project in the computer lab. Later, newfangled _"web"_
servers started popping up using the untested and weird ["Hyper-Text
Transfer Protocol"][26]. These "websites" soon proved their use,
becoming gateways to anonymous [FTP][23] and [gopher][24] sites and
aggregating information on various esoteric topics.

Once you'd deduced the existence and location of software on the early
Internet, your next task was usually porting it to your particular
combination of compiler, operating system and hardware. The early
Internet was not homogenous in composition as it is now; there were
lots of different flavors of [Unix][0], [VMS][1], [OS/2][2] and many
others now [forgotten][3] running on just as many different machines with
varying architectures and capabililites.

The majority of software was written in C which made task of porting
easier, but it was far from simple. You had to work around the
different services offered by different operating system flavors and
different C compiler implementations. Not to mention the different
capabilities offered by different hardware platforms; not everybody
had access to fancy new CD-ROM drives and had to make do with 3.5"
floppy disks. 

After lots of hacking and learning far more about your machine, OS and
compiler than you ever could from reading any book, you finally have a
compiled version of the library that you hope works. 

| "Testing? It compiled didn't it!? Ship it." - Embarassingly, me

You [shim][27] it into your project and get on with whatever it was
you were trying to accomplish. You can see why "roll your own" was a
viable option, sometimes it was easier to just learn how to write the
functionality you needed than to find it on the Internet and get
someone else's software working. That's how we got experts in
cryptography, compression, networking, languages and all the other
things that make computers fun.

Finally, the nightmare scenario. Seven months later after your program
has been put into production and you have moved on to another project
a shadow falls across your desk. There's a bug and it stems from the
library you worked so hard to incorporate into this now-indespensible
application. You again have choices; hope you can fix the library,
hope the library maintainer has fixed the bug and the source is still
accessible, or hope the Internet has offered up a replacement library
in the interim.

Notice there is a lot of hoping there. Hope is not a plan.

## Why Python is Cooler Than Other Language Ecosystems

Python as a language is pretty friendly to new programmers while
providing enough depth and mystique to draw in hard-core nerds. But
the real strength of Python isn't the language, it's the ecosystem
that allows us to flippantly say "Oh, you need a high performance web
server for your new RESTful API? Just `pip install gunicorn`."

Admittedly, the discovery story hasn't improved a whole lot since the
fun-old-days of trawling USENET. It still helps to be plugged into the
Python world thru websites, podcasts, and Slack chats. But when I have
a sudden need for specialized libraries, often the first thing I do is:

```console
$ python3 -m pip list | grep 'weird but helpful topic'
```

and most of the time _something_ shows up in that list! 

The foundational technology that makes all of this magic possible is
the concept and practice of Python packaging.

[0]: Unix
[1]: VMS
[2]: OS/2
[3]: BeOS

[18]: https://en.wikipedia.org/wiki/Not_invented_here
[19]: https://pypi.org
[20]: https://www.pypa.io/en/latest/
[21]: usenet
[22]: irc
[23]: ftp
[24]: gopher
[25]: telnet
[26]: HTTP
[27]: software shim
