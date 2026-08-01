package com.example.bank

import com.example.bank.domain.models.account.BankAccount
import java.math.BigDecimal
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals

class BankAccountTest {

    @Test
    fun withdraw_reduces_balance_by_the_amount() {
        val account = BankAccount("ACC-001", BigDecimal(200))

        account.withdraw(BigDecimal(50))

        assertEquals(BigDecimal(150), account.balance)
    }

    @Test
    fun withdraw_rejects_a_non_positive_amount() {
        val account = BankAccount("ACC-001", BigDecimal(200))

        assertFailsWith<IllegalArgumentException> { account.withdraw(BigDecimal.ZERO) }
    }

    @Test
    fun withdraw_rejects_an_amount_greater_than_the_balance() {
        val account = BankAccount("ACC-001", BigDecimal(200))

        assertFailsWith<IllegalStateException> { account.withdraw(BigDecimal(201)) }
    }

    @Test
    fun accounts_with_the_same_id_are_equal() {
        assertEquals(BankAccount("ACC-001", BigDecimal(1)), BankAccount("ACC-001", BigDecimal(999)))
    }

    @Test
    fun accounts_with_different_ids_are_not_equal() {
        assertNotEquals(BankAccount("ACC-001", BigDecimal(1)), BankAccount("ACC-002", BigDecimal(1)))
    }
}
