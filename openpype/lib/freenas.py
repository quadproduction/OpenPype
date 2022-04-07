"""
Python module to interact with Freenas API through requests
"""

import os
import sys
import argparse
import json

import requests
import urllib3


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

        self._ep = f'http://{hostname}/api/v1.0'

    def __request(self, resource, method='GET', data='', params=''):
        url = f'{self._ep}/{resource}/'
        result = requests.request(
            method,
            url,
            data=json.dumps(data),
            params=params,
            headers={'Content-Type': "application/json"},
            auth=(self._user, self._secret),
            verify=False)

        if result.ok:
            try:
                return result.json()
            except Exception:
                return result.text

        raise ValueError(result)

    def _get_disks(self):
        disks = self.__request('storage/disk')
        return [disk.get('disk_name') for disk in disks]

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
        self.__request(
            'storage/volume',
            method='POST',
            data={
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
        self.__request(f'/storage/dataset/{parent}', method='POST', data=data)

    def create_dataset(self, path, **kwargs):
        names = path.split('/')
        existing_datasets_name = [n.get('name') for n in self._get_datasets()]

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
        data = {
            'mp_path': path,
            'mp_acl': 'unix',
            'mp_mode': '777',
            'mp_user': 'nobody',
            'mp_group': 'nobody',
        }

        if kwargs:
            data.update(kwargs)

        self.__request('storage/permission', method='PUT', data=data)

    def service_start(self, name):
        """
        Start Freenas service

        :param name: Service name to start
        :type name: str
        """
        self.__request(
            f'services/services/{name}',
            method='PUT', 
            data={'srv_enable': True}
        )