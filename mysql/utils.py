import os
# !/bin/python3
# -*- coding: UTF-8 -*-
from ldap3 import Server, Connection, ALL, SUBTREE, ServerPool


class LdapAuth:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.LDAP_SERVER_POOL = ['172.0.25.112']  # 域控服务器ip地址
        self.LDAP_SERVER_PORT = 389  # 端口
        self.ADMIN_DN = 'adjoiner'  # 拥有查询权限的域账号
        self.ADMIN_PASSWORD = '1qaz@WSX'  # 对应的密码
        self.SEARCH_BASE = 'cn=users,dc=oa,dc=caijj,dc=net'

    def ldap_auth(self):
        ldap_server_pool = ServerPool(self.LDAP_SERVER_POOL)
        conn = Connection(ldap_server_pool, user=self.ADMIN_DN, password=self.ADMIN_PASSWORD, check_names=True,
                          lazy=False, raise_exceptions=False)
        conn.open()
        conn.bind()
        search_filter = '(sAMAccountName=%s)' % self.user
        # print (search_filter)
        res = conn.search(
            search_base=self.SEARCH_BASE,
            search_filter=search_filter,  # 值查询一个用户
            # search_filter = '(objectclass=user)',#查询所有用户
            search_scope=SUBTREE,
            attributes=['cn', 'sn', 'givenName', 'mail',
                        'sAMAccountName']  # cn用户中文名，sn姓，givenName名，mail邮件，sAMAccountName是账号
        )
        if res:
            entry = conn.response[0]
            dn = entry['dn']
            conn2 = Connection(ldap_server_pool, user=dn, password=self.password, check_names=True, lazy=False,
                               raise_exceptions=False)
            conn2.bind()
        return conn2.result["description"]


def ccpp():
    main="pt-query-digest --help"
    f = os.popen(main)
    data = f.readlines()
    f.close()
    return data

if __name__=='__main__':
    print(ccpp())
    ldapAuth = LdapAuth('adjoiner', '1qaz@WSX')
    print(ldapAuth.ldap_auth())