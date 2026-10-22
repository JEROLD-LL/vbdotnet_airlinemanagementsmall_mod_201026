Imports System.Security.Cryptography
Imports System.Text
Imports Npgsql

Public Class UserRepository
    Public Shared Function GetByUsername(username As String) As User
        Dim query As String = "SELECT id, username, password, email, full_name, role, created_at FROM ""User"" WHERE username = @username"
        Using reader As NpgsqlDataReader = DatabaseHelper.ExecuteReader(query, New NpgsqlParameter("@username", username))
            If reader.Read() Then
                Return New User With {
                    .Id = reader.GetInt32(0),
                    .Username = reader.GetString(1),
                    .Password = reader.GetString(2),
                    .Email = reader.GetString(3),
                    .FullName = reader.GetString(4),
                    .Role = reader.GetString(5),
                    .CreatedAt = reader.GetDateTime(6)
                }
            End If
        End Using
        Return Nothing
    End Function

    Public Shared Function GetById(id As Integer) As User
        Dim query As String = "SELECT id, username, password, email, full_name, role, created_at FROM ""User"" WHERE id = @id"
        Using reader As NpgsqlDataReader = DatabaseHelper.ExecuteReader(query, New NpgsqlParameter("@id", id))
            If reader.Read() Then
                Return New User With {
                    .Id = reader.GetInt32(0),
                    .Username = reader.GetString(1),
                    .Password = reader.GetString(2),
                    .Email = reader.GetString(3),
                    .FullName = reader.GetString(4),
                    .Role = reader.GetString(5),
                    .CreatedAt = reader.GetDateTime(6)
                }
            End If
        End Using
        Return Nothing
    End Function

    Public Shared Function UsernameExists(username As String) As Boolean
        Dim query As String = "SELECT COUNT(*) FROM ""User"" WHERE username = @username"
        Dim count As Integer = Convert.ToInt32(DatabaseHelper.ExecuteScalar(query, New NpgsqlParameter("@username", username)))
        Return count > 0
    End Function

    Public Shared Function EmailExists(email As String) As Boolean
        Dim query As String = "SELECT COUNT(*) FROM ""User"" WHERE email = @email"
        Dim count As Integer = Convert.ToInt32(DatabaseHelper.ExecuteScalar(query, New NpgsqlParameter("@email", email)))
        Return count > 0
    End Function

    Public Shared Function Create(user As User) As Integer
        Dim query As String = "INSERT INTO ""User"" (username, password, email, full_name, role, created_at) VALUES (@username, @password, @email, @full_name, @role, @created_at) RETURNING id"
        Dim id As Integer = Convert.ToInt32(DatabaseHelper.ExecuteScalar(query,
            New NpgsqlParameter("@username", user.Username),
            New NpgsqlParameter("@password", user.Password),
            New NpgsqlParameter("@email", user.Email),
            New NpgsqlParameter("@full_name", user.FullName),
            New NpgsqlParameter("@role", user.Role),
            New NpgsqlParameter("@created_at", user.CreatedAt)
        ))
        Return id
    End Function

    Public Shared Sub Update(user As User)
        Dim query As String = "UPDATE ""User"" SET email = @email, full_name = @full_name WHERE id = @id"
        DatabaseHelper.ExecuteNonQuery(query,
            New NpgsqlParameter("@email", user.Email),
            New NpgsqlParameter("@full_name", user.FullName),
            New NpgsqlParameter("@id", user.Id)
        )
    End Sub

    Public Shared Sub UpdatePassword(userId As Integer, hashedPassword As String)
        Dim query As String = "UPDATE ""User"" SET password = @password WHERE id = @id"
        DatabaseHelper.ExecuteNonQuery(query,
            New NpgsqlParameter("@password", hashedPassword),
            New NpgsqlParameter("@id", userId)
        )
    End Sub

    Public Shared Function GetAll() As List(Of User)
        Dim users As New List(Of User)
        Dim query As String = "SELECT id, username, password, email, full_name, role, created_at FROM ""User"" ORDER BY created_at DESC"
        Using reader As NpgsqlDataReader = DatabaseHelper.ExecuteReader(query)
            While reader.Read()
                users.Add(New User With {
                    .Id = reader.GetInt32(0),
                    .Username = reader.GetString(1),
                    .Password = reader.GetString(2),
                    .Email = reader.GetString(3),
                    .FullName = reader.GetString(4),
                    .Role = reader.GetString(5),
                    .CreatedAt = reader.GetDateTime(6)
                })
            End While
        End Using
        Return users
    End Function

    Public Shared Function VerifyPassword(plainPassword As String, hashedPassword As String) As Boolean
        Dim hash As String = HashPassword(plainPassword)
        Return hash.Equals(hashedPassword, StringComparison.OrdinalIgnoreCase)
    End Function

    Public Shared Function HashPassword(password As String) As String
        Using sha1 As SHA1 = SHA1.Create()
            Dim hash As Byte() = sha1.ComputeHash(Encoding.UTF8.GetBytes(password))
            Return BitConverter.ToString(hash).Replace("-", "").ToUpper()
        End Using
    End Function
End Class

