FROM maven:3.9-eclipse-temurin-8 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:8-jre
WORKDIR /app
COPY --from=build /src/target/java-deserial-lab-1.0-jar-with-dependencies.jar /app/app.jar
RUN echo "OSWE{java_deserial_lab_flag}" > /flag.txt
EXPOSE 8080
CMD ["java", "-jar", "/app/app.jar"]
