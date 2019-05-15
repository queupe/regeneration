import logging
import random

import server

import env


def create_factory():
    name = env.repair_class
    if name not in globals():
        msg = 'unknown repair behavior (%s)' % name
        logging.fatal(msg)
        raise ValueError(msg)
    return globals()[name].Factory()

class RepairMixin(object):
    def __init__(self):
        


class MBRrepair(BotMixin, FixedRateMixin):  # {{{
    class Factory(object):  # {{{
        def __init__(self, config):
            assert len(config['bot']['params']) == 1
            self.rate = float(config['bot']['params'][0])
            assert len(config['bot']['master']) == 1
            self.rateMaster = float(config['bot']['master'][0])

        def __call__(self, hid):
            if hid == HOST_ID_BOT_MASTER:
                return FixedRateBot(hid, self.rateMaster)
            else:
                return FixedRateBot(hid, self.rate)
    # }}}

    def __init__(self, hid, rate):
        BotMixin.__init__(self)
        FixedRateMixin.__init__(self, rate)
        self.hid = int(hid)
        logging.debug('%s rate %f', self, self.rate)
# }}}
