"""
Python module to interact with Freenas API through requests
"""


import os
import sys
import argparse
import json

import requests
import urllib3

# from ppUtils.ppSettings import SERVER

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FreenasAPI(object):
    """

    """

    def __init__(self, hostname, user, secret):
        """
        Object constructor

        :param hostname: server fqdn
        :type basename: str
        :param user: username used to connected to Freenas API typically 'root'
        :type user: str
        :param secret: password for current user
        :type secret: str
        """
        self._hostname = hostname
        self._user = user
        self._secret = secret

        self._ep = 'http://%s/api/v1.0' % hostname

    def __request(self, resource, method='GET', data=None, params=None):
        if data is None:
            data = ''

        if params is None:
            params = ''

        url = '%s/%s/' % (self._ep, resource)

        r = requests.request(
            method,
            url,
            data=json.dumps(data),
            params=params,
            headers={'Content-Type': "application/json"},
            auth=(self._user, self._secret),
            verify=False)

        if r.ok:
            try:
                return r.json()
            except Exception:
                return r.text

        raise ValueError(r)

    def _get_disks(self):
        disks = self.__request('storage/disk')
        return [disk['disk_name'] for disk in disks]

    def _get_volumes(self):
        volumes = self.__request('storage/volume')
        return volumes

    def _get_datasets(self):
        datasets = self.__request('storage/dataset', params={'limit': 999})
        return datasets

    def _get_nfs_shares(self):
        nfs_shares = self.__request('sharing/nfs')
        return nfs_shares

    def create_pool(self):
        disks = self._get_disks()
        self.__request('storage/volume', method='POST', data={
            'volume_name': 'tank',
            'layout': [
                {'vdevtype': 'stripe', 'disks': disks},
            ],
        })

    def __create_dataset(self, path, **kwargs):
        parent, name = os.path.split(path)
        data = {'name': name}
        if kwargs:
            data.update(kwargs)
        self.__request('/storage/dataset/%s' % parent, method='POST', data=data)

    def create_dataset(self, path, **kwargs):
        names = path.split('/')
        existing_datasets_name = [n['name'] for n in self._get_datasets()]

        for i, _ in enumerate(names):
            dataset_path = "/".join(names[:i + 1])
            if dataset_path not in existing_datasets_name:
                self.__create_dataset(dataset_path, **kwargs)

    def create_nfs_share(self, path, **kwargs):
        data = {}
        data['nfs_paths'] = [path]

        if kwargs:
            data.update(kwargs)

        if not data.get('nfs_security'):
            data['nfs_security'] = 'sys'

        self.__request('sharing/nfs', method='POST', data=data)

    def create_cifs_share(self, path, **kwargs):
        data = {}
        data['cifs_path'] = path

        if kwargs:
            data.update(kwargs)

        self.__request('sharing/cifs', method='POST', data=data)

    def set_permission(self, path, **kwargs):
        data = {}
        data['mp_path'] = path
        data['mp_acl'] = 'unix'
        data['mp_mode'] = '777'
        data['mp_user'] = 'nobody'
        data['mp_group'] = 'nobody'

        if kwargs:
            data.update(kwargs)

        self.__request('storage/permission', method='PUT', data=data)

    def service_start(self, name):
        """
        Start Freenas service

        :param name: Service name to start
        :type name: str
        """
        self.__request('services/services/%s' % name, method='PUT', data={
            'srv_enable': True,
        })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--hostname', required=True, type=str)
    parser.add_argument('-u', '--user', required=True, type=str)
    parser.add_argument('-p', '--passwd', required=True, type=str)

    # args = parser.parse_args(sys.argv[1:])

    # startup = FreenasAPI(args.hostname, args.user, args.passwd)


if __name__ == '__main__':
    main()
