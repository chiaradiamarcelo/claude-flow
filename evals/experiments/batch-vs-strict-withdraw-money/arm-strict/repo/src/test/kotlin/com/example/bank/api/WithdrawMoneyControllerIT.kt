package com.example.bank.api

import com.example.bank.application.WithdrawMoneyUseCase
import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InsufficientFundsException
import com.example.bank.domain.models.account.InvalidWithdrawalAmountException
import org.junit.jupiter.api.Test
import org.mockito.Mockito.verify
import org.mockito.Mockito.verifyNoInteractions
import org.mockito.Mockito.`when`
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.http.MediaType
import org.springframework.test.context.bean.override.mockito.MockitoBean
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.content
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.status
import java.math.BigDecimal

@WebMvcTest(WithdrawMoneyController::class)
class WithdrawMoneyControllerIT {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockitoBean
    private lateinit var withdrawMoney: WithdrawMoneyUseCase

    @Test
    fun returns_200_and_the_new_balance_when_the_withdrawal_succeeds() {
        `when`(withdrawMoney.execute(ACCOUNT_ID, AMOUNT)).thenReturn(Account(ACCOUNT_ID, BigDecimal("150")))

        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"amount":50}"""),
        )

        response.andExpect(status().isOk)
            .andExpect(content().json("""{"accountId":"$ACCOUNT_ID","balance":150}"""))
        verify(withdrawMoney).execute(ACCOUNT_ID, AMOUNT)
    }

    @Test
    fun returns_404_when_the_account_does_not_exist() {
        `when`(withdrawMoney.execute(ACCOUNT_ID, AMOUNT)).thenThrow(AccountNotFoundException(ACCOUNT_ID))

        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"amount":50}"""),
        )

        response.andExpect(status().isNotFound)
    }

    @Test
    fun returns_400_when_the_amount_exceeds_the_balance() {
        `when`(withdrawMoney.execute(ACCOUNT_ID, AMOUNT)).thenThrow(InsufficientFundsException(ACCOUNT_ID, AMOUNT))

        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"amount":50}"""),
        )

        response.andExpect(status().isBadRequest)
    }

    @Test
    fun returns_400_when_the_amount_is_not_positive() {
        `when`(withdrawMoney.execute(ACCOUNT_ID, BigDecimal.ZERO))
            .thenThrow(InvalidWithdrawalAmountException(BigDecimal.ZERO))

        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"amount":0}"""),
        )

        response.andExpect(status().isBadRequest)
    }

    @Test
    fun returns_400_when_the_amount_field_is_missing() {
        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"),
        )

        response.andExpect(status().isBadRequest)
        verifyNoInteractions(withdrawMoney)
    }

    @Test
    fun returns_500_when_the_use_case_fails_unexpectedly() {
        `when`(withdrawMoney.execute(ACCOUNT_ID, AMOUNT)).thenThrow(RuntimeException("boom"))

        val response = mockMvc.perform(
            post("/accounts/$ACCOUNT_ID/withdrawals")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"amount":50}"""),
        )

        response.andExpect(status().isInternalServerError)
    }
}

private const val ACCOUNT_ID = "ACC-001"
private val AMOUNT = BigDecimal("50")
