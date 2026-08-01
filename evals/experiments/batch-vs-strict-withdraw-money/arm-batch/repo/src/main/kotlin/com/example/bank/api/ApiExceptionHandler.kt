package com.example.bank.api

import com.example.bank.api.dto.ErrorResponse
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InsufficientFundsException
import com.example.bank.domain.models.account.InvalidWithdrawalAmountException
import org.springframework.http.HttpStatus
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.ResponseStatus
import org.springframework.web.bind.annotation.RestControllerAdvice

/** Centralizes every exception → HTTP status mapping for the API layer. */
@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(AccountNotFoundException::class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    fun handleAccountNotFound(exception: AccountNotFoundException): ErrorResponse =
        ErrorResponse("ACCOUNT_NOT_FOUND", exception.message)

    @ExceptionHandler(InsufficientFundsException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun handleInsufficientFunds(exception: InsufficientFundsException): ErrorResponse =
        ErrorResponse("INSUFFICIENT_FUNDS", exception.message)

    @ExceptionHandler(InvalidWithdrawalAmountException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun handleInvalidWithdrawalAmount(exception: InvalidWithdrawalAmountException): ErrorResponse =
        ErrorResponse("INVALID_WITHDRAWAL_AMOUNT", exception.message)

    @ExceptionHandler(HttpMessageNotReadableException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun handleUnreadableRequest(exception: HttpMessageNotReadableException): ErrorResponse =
        ErrorResponse("MALFORMED_REQUEST", "The request body could not be read")

    @ExceptionHandler(RuntimeException::class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    fun handleUnexpectedFailure(exception: RuntimeException): ErrorResponse =
        ErrorResponse("INTERNAL_ERROR", "The withdrawal could not be processed")
}
