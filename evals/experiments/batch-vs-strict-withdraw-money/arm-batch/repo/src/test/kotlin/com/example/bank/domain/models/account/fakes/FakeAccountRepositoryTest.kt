package com.example.bank.domain.models.account.fakes

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContractTest

class FakeAccountRepositoryTest : AccountRepositoryContractTest() {

    override fun newRepository(): AccountRepository = FakeAccountRepository()
}
