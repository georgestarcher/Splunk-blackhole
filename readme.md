# App setup on Debian Jessie / Raspbian Jessie 

Author: Duane Waddle (duckfez)

This code is presented **AS IS** under MIT license.

##Summary:

This code project demonstrates using Splunk KVStore and quagga on a Raspberry Pi to blackhole routing from Splunk. 

##Usage:

As root:

	apt-get install quagga

	Edit /etc/quagga/daemons:  
	zebra=yes
	bgpd=yes
	ospfd=yes

	cd /etc/quagga
	cp -p /usr/share/doc/quagga/examples/zebra.conf.sample ./zebra.conf
	cp -p /usr/share/doc/quagga/examples/bgpd.conf.sample ./bgpd.conf
	cp -p /usr/share/doc/quagga/examples/ospfd.conf.sample ./ospfd.conf
	chown quagga zebra.conf bgpd.conf ospfd.conf

	systemctl enable
	systemctl restart quagga

	usermod -aG quaggavty $USER_RUNNING_BLACKHOLE


Now basic Quagga should be working.  You'll need to integrate it into your BGP/IGP
and redistribute static routes into the routing domain.

The "splunk_app" dir has an app with the KV store collection definition stuff in it.
It goes on a search head.

