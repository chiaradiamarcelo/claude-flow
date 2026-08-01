package com.example.bank.domain.models.account

/** Write-side port for the [Account] aggregate. */
interface AccountRepository {

    fun save(account: Account)

    fun findById(accountId: String): Account?
}
