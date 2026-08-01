package com.example.bank.domain.models.account.fakes

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository

class FakeAccountRepository : AccountRepository {

    private val accounts: MutableMap<String, Account> = mutableMapOf()

    fun seed(account: Account) {
        accounts[account.accountId] = account
    }

    override fun findById(accountId: String): Account? = accounts[accountId]

    override fun save(account: Account): Account {
        accounts[account.accountId] = account

        return account
    }
}
