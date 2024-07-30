from datetime import datetime, timedelta
from shared import OPAYGOShared
from decode_token import OPAYGODecoder
from encode_token import OPAYGOEncoder

class DeviceSimulator(object):

    def __init__(self, starting_code, key, starting_count=1, restricted_digit_set=False, waiting_period_enabled=True, time_divider=1):
        self.starting_code = starting_code
        self.key = key
        self.time_divider = time_divider
        self.restricted_digit_set = restricted_digit_set
        self.waiting_period_enabled = waiting_period_enabled  # Should always be true except for testing

        self.payg_enabled = True
        self.count = starting_count
        self.expiration_date = datetime.now()
        self.invalid_token_count = 0
        self.token_entry_blocked_until = datetime.now()
        self.used_counts = []

    def print_status(self):
        print('-------------------------')
        print('Expiration Date: '+ str(self.expiration_date))
        print('Current count: '+str(self.count))
        print('PAYG Enabled: '+str(self.payg_enabled))
        print('Active: '+str(self.is_active()))
        print('-------------------------')

    def is_active(self):
        return self.expiration_date > datetime.now()

    def enter_token(self, token, show_result=True):
        if len(token) == 9:
            token_int = int(token)
            return self._update_device_status_from_token(token_int, show_result)
        else:
            token_int = int(token)
            return self._update_device_status_from_extended_token(token_int, show_result)

    def get_days_remaining(self):
        if self.payg_enabled:
            td = self.expiration_date - datetime.now()
            days, hours, minutes = td.days, td.seconds//3600, (td.seconds//60)%60
            days = days + (hours + minutes/60)/24
            return round(days)
        else:
            return 'infinite'

    def _update_device_status_from_token(self, token, show_result=True):
        if self.token_entry_blocked_until > datetime.now() and self.waiting_period_enabled:
            if show_result:
                print('TOKEN_ENTRY_BLOCKED')
            return False
        token_value, token_count, token_type = OPAYGODecoder.get_activation_value_count_and_type_from_token(
            token=token,
            starting_code=self.starting_code,
            key=self.key,
            last_count=self.count,
            restricted_digit_set=self.restricted_digit_set,
            used_counts=self.used_counts
        )
        if token_value is None:
            if show_result:
                print('TOKEN_INVALID')
            self.invalid_token_count += 1
            self.token_entry_blocked_until = datetime.now() + timedelta(minutes=2**self.invalid_token_count)
            return -1
        elif token_value == -2:
            if show_result:
                print('OLD_TOKEN')
            return -2
        else:
            if show_result:
                print('TOKEN_VALID', ' | Value:', token_value)
            if token_count > self.count or token_value == OPAYGOShared.COUNTER_SYNC_VALUE:
                self.count = token_count
            self.used_counts = OPAYGODecoder.update_used_counts(self.used_counts, token_value, token_count, token_type)
            self.invalid_token_count = 0
            self._update_device_status_from_token_value(token_value, token_type)
            return 1

    def _update_device_status_from_extended_token(self, token):
        if self.token_entry_blocked_until > datetime.now() and self.waiting_period_enabled:
            print('TOKEN_ENTRY_BLOCKED')
        token_value, token_count = OPAYGODecoder.get_activation_value_count_from_extended_token(
            token=token,
            starting_code=self.starting_code,
            key=self.key,
            last_count=self.count,
            restricted_digit_set=self.restricted_digit_set
        )
        if token_value is None:
            print('TOKEN_INVALID')
            self.invalid_token_count += 1
            self.token_entry_blocked_until = datetime.now() + timedelta(minutes=2**self.invalid_token_count)
        else:
            print('Special token entered, value: '+str(token_value))

    def _update_device_status_from_token_value(self, token_value, token_type):
        if token_value <= OPAYGOShared.MAX_ACTIVATION_VALUE:
            if not self.payg_enabled and token_type == OPAYGOShared.TOKEN_TYPE_SET_TIME:
                self.payg_enabled = True
            if self.payg_enabled:
                self._update_expiration_date_from_value(token_value, token_type)
        elif token_value == OPAYGOShared.PAYG_DISABLE_VALUE:
            self.payg_enabled = False
        elif token_value != OPAYGOShared.COUNTER_SYNC_VALUE:
            # We do nothing if its the sync counter value, the counter has been synced already
            print('COUNTER_SYNCED')
        else:
            # If it's another value we also do nothing, as they are not defined
            print('UNKNOWN_COMMAND')

    def _update_expiration_date_from_value(self, toke_value, token_type):
        number_of_days = toke_value/self.time_divider
        if token_type == OPAYGOShared.TOKEN_TYPE_SET_TIME:
            self.expiration_date = datetime.now() + timedelta(days=number_of_days)
        else:
            if self.expiration_date < datetime.now():
                self.expiration_date = datetime.now()
            self.expiration_date = self.expiration_date + timedelta(days=number_of_days)

class SingleDeviceServerSimulator(object):

    def __init__(self, starting_code, key, starting_count=1, restricted_digit_set=False, time_divider=1):
        self.starting_code = starting_code
        self.key = key
        self.count = starting_count
        self.expiration_date = datetime.now()
        self.furthest_expiration_date = datetime.now()
        self.payg_enabled = True
        self.time_divider = time_divider
        self.restricted_digit_set = restricted_digit_set

    def print_status(self):
        print('Expiration Date: '+ str(self.expiration_date))
        print('Current count: '+str(self.count))
        print('PAYG Enabled: '+str(self.payg_enabled))

    def generate_payg_disable_token(self):
        self.count, token = OPAYGOEncoder.generate_standard_token(
            starting_code=self.starting_code,
            key=self.key,
            value=OPAYGOShared.PAYG_DISABLE_VALUE,
            count=self.count,
            restricted_digit_set=self.restricted_digit_set
        )
        return SingleDeviceServerSimulator._format_token(token)

    def generate_counter_sync_token(self):
        self.count, token = OPAYGOEncoder.generate_standard_token(
            starting_code=self.starting_code,
            key=self.key,
            value=OPAYGOShared.COUNTER_SYNC_VALUE,
            count=self.count,
            restricted_digit_set=self.restricted_digit_set
        )
        return SingleDeviceServerSimulator._format_token(token)

    def generate_token_from_date(self, new_expiration_date, force=False):
        furthest_expiration_date = self.furthest_expiration_date
        if new_expiration_date > self.furthest_expiration_date:
            self.furthest_expiration_date = new_expiration_date

        if new_expiration_date > furthest_expiration_date:
            # If the date is strictly above the furthest date activated, use ADD
            value = self._get_value_to_activate(new_expiration_date, self.expiration_date, force)
            self.expiration_date = new_expiration_date
            return self._generate_token_from_value(value, mode=OPAYGOShared.TOKEN_TYPE_ADD_TIME)
        else:
            # If the date is below or equal to the furthest date activated, use SET
            value = self._get_value_to_activate(new_expiration_date, datetime.now(), force)
            self.expiration_date = new_expiration_date
            return self._generate_token_from_value(value, mode=OPAYGOShared.TOKEN_TYPE_SET_TIME)

    def _generate_token_from_value(self, value, mode):
        self.count, token = OPAYGOEncoder.generate_standard_token(
            starting_code=self.starting_code,
            key=self.key,
            value=value,
            count=self.count,
            mode=mode,
            restricted_digit_set=self.restricted_digit_set
        )
        return SingleDeviceServerSimulator._format_token(token)

    def _generate_extended_value_token(self, value):
        pass

    def _get_value_to_activate(self, new_time, reference_time, force_maximum=False):
        if new_time <= reference_time:
            return 0
        else:
            days = self._timedelta_to_days(new_time - reference_time)
            value = int(round(days*self.time_divider, 0))
            if value > OPAYGOShared.MAX_ACTIVATION_VALUE:
                if not force_maximum:
                    raise Exception('TOO_MANY_DAYS_TO_ACTIVATE')
                else:
                    return OPAYGOShared.MAX_ACTIVATION_VALUE  # Will need to be activated again after those days
            return value

    @staticmethod
    def _timedelta_to_days(this_timedelta):
        return this_timedelta.days + (this_timedelta.seconds / 3600 / 24)

    @staticmethod
    def _format_token(token):
        token = str(token)
        if len(token) < 9:
            token = '0' * (9 - len(token)) + token
        return token
