Imports System.Text.RegularExpressions
Imports Npgsql

Public Class BookingService
    ' High Complexity: Transaction Management Pattern for atomic operations
    Public Shared Function CreateBooking(flightId As Integer, userId As Integer?, passengerName As String, passengerEmail As String, seatNumber As String) As String
        Dim errors As New List(Of String)

        ' Validation
        If String.IsNullOrWhiteSpace(passengerName) Then
            errors.Add("Passenger name is required.")
        ElseIf passengerName.Length < 2 OrElse passengerName.Length > 255 Then
            errors.Add("Passenger name must be between 2 and 255 characters.")
        ElseIf Not Regex.IsMatch(passengerName, "^[a-zA-Z\s'-]+$") Then
            errors.Add("Passenger name can only contain letters, spaces, hyphens, and apostrophes.")
        End If

        If String.IsNullOrWhiteSpace(passengerEmail) Then
            errors.Add("Email is required.")
        ElseIf Not Regex.IsMatch(passengerEmail, "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$") Then
            errors.Add("Invalid email format.")
        ElseIf passengerEmail.Length > 255 Then
            errors.Add("Email must be 255 characters or less.")
        End If

        If Not String.IsNullOrWhiteSpace(seatNumber) Then
            If seatNumber.Length > 10 Then
                errors.Add("Seat number must be 10 characters or less.")
            ElseIf Not Regex.IsMatch(seatNumber, "^[0-9]{1,3}[A-Z]{1,2}$", RegexOptions.IgnoreCase) Then
                errors.Add("Seat number format is invalid. Use format like '12A' or '123AB'.")
            End If
        End If

        If errors.Count > 0 Then
            Return String.Join(" ", errors)
        End If

        ' Transaction Management Pattern - Atomic operation
        Dim transaction As NpgsqlTransaction = Nothing
        Try
            transaction = DatabaseHelper.BeginTransaction()

            ' Lock flight row for update
            Dim flight As Flight = FlightRepository.LockForUpdate(flightId, transaction)
            If flight Is Nothing Then
                transaction.Rollback()
                Return "Flight not found."
            End If

            ' Re-check available seats
            If flight.AvailableSeats < 1 Then
                transaction.Rollback()
                Return "No available seats on this flight."
            End If

            ' Create booking
            Dim booking As New Booking With {
                .FlightId = flightId,
                .UserId = userId,
                .PassengerName = passengerName,
                .PassengerEmail = passengerEmail,
                .SeatNumber = If(String.IsNullOrWhiteSpace(seatNumber), String.Empty, seatNumber.ToUpper()),
                .BookingDate = DateTime.Now
            }
            BookingRepository.Create(booking, transaction)

            ' Decrement seats
            FlightRepository.DecrementSeats(flightId, transaction)

            ' Commit transaction
            transaction.Commit()
            Return Nothing ' Success
        Catch ex As Exception
            If transaction IsNot Nothing Then
                transaction.Rollback()
            End If
            Return "An error occurred while creating the booking: " & ex.Message
        End Try
    End Function

    ' High Complexity: Transaction Management Pattern for atomic operations
    Public Shared Function DeleteBooking(bookingId As Integer, userId As Integer) As String
        ' Verify booking exists and belongs to user
        Dim booking As Booking = BookingRepository.GetById(bookingId)
        If booking Is Nothing Then
            Return "Booking not found."
        End If

        If booking.UserId.HasValue AndAlso booking.UserId.Value <> userId Then
            Return "Access denied. You can only delete your own bookings."
        End If

        ' Transaction Management Pattern - Atomic operation
        Dim transaction As NpgsqlTransaction = Nothing
        Try
            transaction = DatabaseHelper.BeginTransaction()

            ' Delete booking
            BookingRepository.Delete(bookingId, transaction)

            ' Increment seats
            FlightRepository.IncrementSeats(booking.FlightId, transaction)

            ' Commit transaction
            transaction.Commit()
            Return Nothing ' Success
        Catch ex As Exception
            If transaction IsNot Nothing Then
                transaction.Rollback()
            End If
            Return "An error occurred while deleting the booking: " & ex.Message
        End Try
    End Function
End Class

