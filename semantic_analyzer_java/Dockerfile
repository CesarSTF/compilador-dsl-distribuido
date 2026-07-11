FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /app/target/semantic-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar ./semantic.jar
EXPOSE 8080
CMD ["java", "-jar", "semantic.jar"]
