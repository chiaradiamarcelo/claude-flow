package com.example.bank.domain.models.account

interface AccountRepository {

    fun findById(accountId: String): Account?

    fun save(account: Account): Account
}
