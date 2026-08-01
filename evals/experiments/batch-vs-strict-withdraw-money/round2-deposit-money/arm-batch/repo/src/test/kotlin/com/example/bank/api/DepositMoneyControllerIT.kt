package com.example.bank.api

import com.example.bank.application.DepositMoneyUseCase
import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import org.junit.jupiter.api.Test
import org.mockito.BDDMockito.given
import org.mockito.Mockito.verify
import org.mockito.Mockito.verifyNoInteractions
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.http.MediaType.APPLICATION_JSON
import org.springframework.test.context.bean.override.mockito.MockitoBean
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.status
import java.math.BigDecimal

private const val ACCOUNT_ID = "ACC-001"
private const val UNKNOWN_ACCOUNT_ID = "ACC-404"
private val AMOUNT = BigDecimal("50")

@WebMvcTest(DepositMoneyController::class)
class DepositMoneyControllerIT {

    @Autowired
    private lateinit var client: MockMvc

    @MockitoBean
    private lateinit var depositMoney: DepositMoneyUseCase

    @Test
    fun returns_200_and_the_updated_balance_when_the_deposit_succeeds() {
        given(depositMoney.deposit(ACCOUNT_ID, AMOUNT)).willReturn(Account(ACCOUNT_ID, BigDecimal("250")))

        val response = client.perform(
            post("/accounts/$ACCOUNT_ID/deposits")
                .contentType(APPLICATION_JSON)
                .content("""{"amount": 50}"""),
        )

        response.andExpect(status().isOk)
            .andExpect(jsonPath("$.accountId").value(ACCOUNT_ID))
            .andExpect(jsonPath("$.balance").value(250))
        verify(depositMoney).deposit(ACCOUNT_ID, AMOUNT)
    }

    @Test
    fun returns_400_when_the_request_body_amount_is_not_a_number() {
        val response = client.perform(
            post("/accounts/$ACCOUNT_ID/deposits")
                .contentType(APPLICATION_JSON)
                .content("""{"amount": "abc"}"""),
        )

        response.andExpect(status().isBadRequest)
        verifyNoInteractions(depositMoney)
    }

    @Test
    fun returns_400_when_the_deposit_amount_is_not_positive() {
        given(depositMoney.deposit(ACCOUNT_ID, BigDecimal.ZERO))
            .willThrow(InvalidDepositAmountException(BigDecimal.ZERO))

        val response = client.perform(
            post("/accounts/$ACCOUNT_ID/deposits")
                .contentType(APPLICATION_JSON)
                .content("""{"amount": 0}"""),
        )

        response.andExpect(status().isBadRequest)
        verify(depositMoney).deposit(ACCOUNT_ID, BigDecimal.ZERO)
    }

    @Test
    fun returns_404_when_the_account_does_not_exist() {
        given(depositMoney.deposit(UNKNOWN_ACCOUNT_ID, AMOUNT))
            .willThrow(AccountNotFoundException(UNKNOWN_ACCOUNT_ID))

        val response = client.perform(
            post("/accounts/$UNKNOWN_ACCOUNT_ID/deposits")
                .contentType(APPLICATION_JSON)
                .content("""{"amount": 50}"""),
        )

        response.andExpect(status().isNotFound)
    }

    @Test
    fun returns_500_when_the_deposit_fails_unexpectedly() {
        given(depositMoney.deposit(ACCOUNT_ID, AMOUNT)).willThrow(RuntimeException("boom"))

        val response = client.perform(
            post("/accounts/$ACCOUNT_ID/deposits")
                .contentType(APPLICATION_JSON)
                .content("""{"amount": 50}"""),
        )

        response.andExpect(status().isInternalServerError)
    }
}
