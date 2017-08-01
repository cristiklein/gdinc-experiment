Introduction
============
This respository contains experimental artefacts for reproducting the results published in the following [SoCC 2017](https://acmsocc.github.io/2017/) paper:

> Incentivizing Self-Resource-Capping with Graceful Degradation
Mohammad Shahrad (Princeton University); Cristian Klein (Umeå University); Liang Zheng, Mung Chiang (Princeton University); Erik Elmroth (Umeå University); David Wentzlaff (Princeton University)

They are meant to be both human readable and machine executable. If you are familiar with [Docker](https://www.docker.com/), [Ansible](https://www.ansible.com/), [bash](https://www.gnu.org/software/bash/), [Python](https://www.python.org/), [Xen](https://www.xenproject.org/) and [httpmon](https://github.com/cloud-control/httpmon), then you should find no surprises. Nevertheless, you if bump into problems, please contact us.

Prerequisites
=============
You need to have at least two machines:

* The control machine, on which you execute the scripts in the root of this repository.
* The worker machine, on which the experiment will actually run (update `hosts` accordingly).

Both machines need to run Ubuntu 16.04 LTS. Please let us know if the scripts also work for other distributions.

For the control machine, make sure you have [Docker](https://get.docker.com/) and an [SSH agent](https://en.wikipedia.org/wiki/ssh-agent).

For the worker machine, make sure you have public-key root access from the control machine as follows:

```bash
ssh machine-01
sudo su - root
ssh-keygen                    # creates .ssh
cat >> .ssh/authorized_keys   # paste the public key on your control machine
```

Usage
=====

* `./deploy.sh`: deploys the whole experiment. You need to run this script at least once and every time you update the experiment. **NOTICE: The first time you run this script, the RUBiS database is imported from a SQL dump. This may take as much as 30 minutes.**
* `./run-experiment.sh`: runs the experiment and gathers results in a TAR file on the control machine.
* `./experiment-to-csvs.py TARFILE`: converts TARFILE into a CSV that can be used for plotting.

Advanced Usage
==============
Once you are familiar with the repository, you may save some time by only updating the part of the experiment that you actually changed. Make sure you understand what you are doing!

* `./update-containers.sh`: only update containers on worker machine.
* `./run-experiment.sh`: updates the resource manager and workloads before running experiments.

If you change the load traces in `roles/clients/files/workloads/cpu_usage_*.csv`, you must run `./update-workloads.sh`.

Contact
=======
We did our best to make the ride as smooth as possible, then again, to err is human. For questions or feedback, please contact Cristian Klein <cklein@cs.umu.se>.
