package com.example.bank

import com.example.bank.application.WithdrawMoneyUseCase
import com.example.bank.domain.models.account.BankAccount
import com.example.bank.domain.models.account.BankAccountRepository
import java.math.BigDecimal
import kotlin.test.Test
import kotlin.test.assertEquals

class FakeBankAccountRepository(seed: BankAccount) : BankAccountRepository {
    private val store = mutableMapOf(seed.id to seed)
    override fun findById(id: String): BankAccount = store.getValue(id)
    override fun save(account: BankAccount) { store[account.id] = account }
}

class WithdrawMoneyUseCaseTest {

    @Test
    fun withdrawing_reduces_and_returns_the_persisted_balance() {
        val repository = FakeBankAccountRepository(BankAccount("ACC-001", BigDecimal(200)))
        val useCase = WithdrawMoneyUseCase(repository)

        val remaining = useCase.execute("ACC-001", BigDecimal(50))

        assertEquals(BigDecimal(150), remaining)
    }
}
